"""
advanced_predict.py
────────────────────
Primary: TensorFlow MobileNetV2 multiclass model (best_model.keras, 77 classes).
Fallback: Pure-OpenCV heuristic when TF / model file is missing.
          Uses HSV colour analysis to estimate Healthy vs Diseased.
          This keeps the app fully functional without the model file.

PREPROCESSING ARCHITECTURE NOTE (important for patent and retraining):
  This module applies a SAFE colour-mask centre-crop before inference.
  It does NOT apply CLAHE or GrabCut background-removal, because those
  operations change pixel intensity distribution and require the model
  to have been trained on similarly-processed images to be beneficial.
  When a retrained model is available (trained with CLAHE + bg-removal
  augmentation), enable full preprocessing via image_preprocess.py.
"""
import logging
import json
import cv2
import numpy as np
import os

logger = logging.getLogger(__name__)

BASE_PATH        = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH       = os.path.join(BASE_PATH, "models", "best_model.keras")
CLASS_NAMES_PATH = os.path.join(BASE_PATH, "models", "class_names.json")

model        = None
_tf_ok       = None   # None=untested, True=available, False=unavailable
_class_names = None   # cached {index: label} dict


# ── TensorFlow availability check ─────────────────────────────────────────────
def _check_tf() -> bool:
    global _tf_ok
    if _tf_ok is not None:
        return _tf_ok
    try:
        import tensorflow  # noqa
        _tf_ok = True
    except ImportError:
        logger.warning("TensorFlow not installed — using CV fallback for leaf analysis.")
        _tf_ok = False
    return _tf_ok


def load_model_once():
    global model
    if model is not None:
        return
    if not _check_tf():
        raise ImportError("TensorFlow not available")
    import tensorflow as tf
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Leaf model not found at: {MODEL_PATH}\n"
            "Download best_model.keras and place it in the models/ folder."
        )
    model = tf.keras.models.load_model(MODEL_PATH)
    n_out = model.output_shape[-1]
    n_cls = len(_load_class_names())
    if n_out != n_cls:
        logger.error(
            "⚠️  MODEL/CLASS_NAMES MISMATCH: model has %d output neurons "
            "but class_names.json has %d entries. "
            "Predictions for classes beyond index %d will fail to resolve. "
            "Re-export class_names.json from training code to fix this.",
            n_out, n_cls, n_cls - 1
        )
    else:
        logger.info("✅ Leaf model loaded: %d classes, input %s", n_out, model.input_shape)


def _load_class_names() -> dict:
    """Cache and return {index(int): label(str)} from class_names.json,
    skipping the non-class 'disease_bands' metadata key."""
    global _class_names
    if _class_names is not None:
        return _class_names
    if not os.path.exists(CLASS_NAMES_PATH):
        logger.warning("class_names.json not found — cannot map predictions to labels.")
        _class_names = {}
        return _class_names
    try:
        raw = json.load(open(CLASS_NAMES_PATH))
        _class_names = {int(k): v for k, v in raw.items() if k != "disease_bands"}
    except Exception as e:
        logger.warning("Failed to load class_names.json: %s", e)
        _class_names = {}
    return _class_names


# ── Safe colour-mask centre crop ──────────────────────────────────────────────
def _colour_mask_crop(img_bgr: np.ndarray) -> np.ndarray:
    """
    Crop to the dominant leaf region using a HSV colour mask (green + brown +
    yellow pixels).  No pixel values are modified — this is a pure geometric
    operation and is safe regardless of how the model was trained.

    Why this instead of GrabCut:
      GrabCut uses a GMM that frequently misclassifies brown/yellow disease
      lesions as 'background' (they share colours with soil), destroying the
      exact disease signal the model needs.  Colour-mask crop keeps all leaf
      and disease pixels and removes only clearly non-leaf background.

    Returns the cropped BGR array (not resized — caller resizes to 224×224).
    """
    h, w = img_bgr.shape[:2]
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    # Green (healthy leaf tissue)
    green  = cv2.inRange(hsv, np.array([25, 25, 25]),  np.array([95, 255, 255]))
    # Brown (disease lesions, dried tissue)
    brown  = cv2.inRange(hsv, np.array([8,  35, 35]),  np.array([30, 255, 220]))
    # Yellow (chlorosis, early lesions)
    yellow = cv2.inRange(hsv, np.array([20, 40, 40]),  np.array([35, 255, 255]))

    leaf_mask = cv2.bitwise_or(cv2.bitwise_or(green, brown), yellow)

    # Morphological cleanup — fill small holes, remove tiny noise blobs
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    leaf_mask = cv2.morphologyEx(leaf_mask, cv2.MORPH_CLOSE, kernel)
    leaf_mask = cv2.morphologyEx(leaf_mask, cv2.MORPH_OPEN,
                                  cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))

    contours, _ = cv2.findContours(leaf_mask, cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        largest    = max(contours, key=cv2.contourArea)
        area_frac  = cv2.contourArea(largest) / (w * h)

        # Only use the crop if the detected region is meaningful in size
        # (between 8% and 95% of the frame).  If the leaf fills the entire
        # frame or is tiny, fall back to a simple centre crop.
        if 0.08 <= area_frac <= 0.95:
            x, y, cw, ch = cv2.boundingRect(largest)
            # Add 5% padding on each side so we don't clip leaf edges
            pad = int(min(cw, ch) * 0.05)
            x   = max(0, x - pad)
            y   = max(0, y - pad)
            cw  = min(w - x, cw + 2 * pad)
            ch  = min(h - y, ch + 2 * pad)
            cropped = img_bgr[y:y + ch, x:x + cw]
            if cropped.size > 0:
                return cropped

    # Fallback: 85% centre crop (removes frame edges / camera vignette)
    cy, cx = int(h * 0.075), int(w * 0.075)
    return img_bgr[cy:h - cy, cx:w - cx]


# ── Severity from colour (shared by both paths) ───────────────────────────────
def calculate_severity(img_rgb: np.ndarray) -> float:
    """Estimate disease severity from brown/yellow pixel fraction."""
    hsv  = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(hsv, np.array([10, 50, 50]), np.array([35, 255, 255]))
    return float(np.sum(mask > 0)) / float(mask.size) * 100


# ── CV-only fallback ──────────────────────────────────────────────────────────
def _cv_predict(image_path: str) -> dict:
    """
    Heuristic leaf analysis using only OpenCV — no model required.
    Estimates health from the ratio of green vs brown/yellow pixels.
    Confidence is capped at 75% to signal that this is a heuristic estimate,
    not a CNN classification.
    """
    img = cv2.imread(image_path)
    if img is None:
        return {"label": "Error", "confidence": 0.0, "severity": 0.0,
                "severity_level": "None", "error": "Cannot read image"}

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    rgb = cv2.resize(rgb, (224, 224))
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)

    # Green pixels (healthy leaf tissue)
    green_mask  = cv2.inRange(hsv, np.array([28, 30, 30]), np.array([92, 255, 255]))
    green_ratio = float(np.sum(green_mask > 0)) / float(green_mask.size)

    # Brown / yellow pixels (diseased tissue)
    brown_mask  = cv2.inRange(hsv, np.array([10, 50, 50]), np.array([35, 255, 255]))
    brown_ratio = float(np.sum(brown_mask > 0)) / float(brown_mask.size)

    severity = brown_ratio * 100

    if brown_ratio > 0.08:
        label      = "Diseased"
        confidence = min(50.0 + brown_ratio * 200, 75.0)
    else:
        label      = "Healthy"
        confidence = min(50.0 + green_ratio * 100, 75.0)

    if label == "Healthy":
        severity = 0.0
        level    = "None"
    elif severity < 10:
        level = "Low"
    elif severity < 30:
        level = "Moderate"
    else:
        level = "Severe"

    return {
        "label":          label,
        "confidence":     round(confidence, 2),
        "severity":       round(severity, 2),
        "severity_level": level,
        "source":         "cv_fallback",
        "source_note": (
            "TensorFlow model unavailable — colour-analysis fallback used. "
            "Results may differ between devices. Install TensorFlow for "
            "consistent, accurate disease classification."
        ),
    }


# ── Main entry point ──────────────────────────────────────────────────────────
def predict_leaf(image_path: str) -> dict:
    # ── Try TensorFlow multiclass model ───────────────────────────────────
    if _check_tf() and os.path.exists(MODEL_PATH):
        try:
            from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
            load_model_once()
            class_names = _load_class_names()

            img_bgr = cv2.imread(image_path)
            if img_bgr is None:
                return {"label": "Error", "confidence": 0.0,
                        "severity": 0.0, "severity_level": "None"}

            # ── Safe leaf-region crop (pure geometry, zero pixel-value change) ──
            # This removes irrelevant background (soil, sky, other crops) that
            # was NOT present in PlantVillage training images, reducing the
            # domain shift between training and real-world inference.
            # GrabCut is deliberately NOT used here — see docstring on
            # _colour_mask_crop() for the technical reason.
            img_bgr_cropped = _colour_mask_crop(img_bgr)

            rgb          = cv2.cvtColor(img_bgr_cropped, cv2.COLOR_BGR2RGB)
            rgb          = cv2.resize(rgb, (224, 224))
            original_rgb = rgb.copy()   # used for severity calculation

            # ── Test-Time Augmentation (TTA) ──────────────────────────────
            # Average predictions across 5 augmented views of the same image.
            # Real-world photos have arbitrary crop/flip/brightness relative to
            # training — averaging smooths out the influence of any single
            # unlucky framing.  No retraining required; inference-only change.
            # All 5 views are generated from the SAME cropped+resized base
            # so augmentation operates on clean leaf content, not background.
            views = [rgb]                                          # 1. original crop

            h, w  = rgb.shape[:2]
            ch, cw = int(h * 0.85), int(w * 0.85)
            y0, x0 = (h - ch) // 2, (w - cw) // 2
            views.append(
                cv2.resize(rgb[y0:y0 + ch, x0:x0 + cw], (224, 224))
            )                                                      # 2. tighter centre crop

            views.append(cv2.flip(rgb, 1))                        # 3. horizontal flip

            views.append(
                np.clip(rgb.astype(np.float32) * 1.2, 0, 255).astype(np.uint8)
            )                                                      # 4. brighter

            views.append(
                np.clip(rgb.astype(np.float32) * 0.8, 0, 255).astype(np.uint8)
            )                                                      # 5. darker

            batch     = np.stack(
                [preprocess_input(v.astype(np.float32)) for v in views], axis=0
            )
            all_preds = model.predict(batch, verbose=0)           # shape (5, 77)
            preds     = all_preds.mean(axis=0)                    # average softmax
            class_idx = int(np.argmax(preds))
            confidence = float(preds[class_idx]) * 100

            label = class_names.get(class_idx)
            if label is None:
                logger.warning(
                    "Predicted class index %d has no entry in class_names.json "
                    "(%d entries loaded) — falling back to CV heuristic.",
                    class_idx, len(class_names)
                )
                raise KeyError(f"No label for class index {class_idx}")

            severity   = calculate_severity(original_rgb)
            is_healthy = "healthy" in label.lower()

            if is_healthy:
                severity = 0.0
                level    = "None"
            elif severity < 10:
                level = "Low"
            elif severity < 30:
                level = "Moderate"
            else:
                level = "Severe"

            return {
                "label":          label,
                "confidence":     float(round(confidence, 2)),
                "severity":       float(round(severity, 2)),
                "severity_level": str(level),
                "source":         "multiclass_model",
                "class_index":    class_idx,
            }

        except FileNotFoundError as e:
            logger.warning("Model file missing — using CV fallback. %s", e)
        except Exception as e:
            logger.warning("TF predict failed — using CV fallback. %s", e)

    # ── CV fallback ───────────────────────────────────────────────────────
    logger.info("Using OpenCV heuristic fallback for leaf analysis.")
    return _cv_predict(image_path)
