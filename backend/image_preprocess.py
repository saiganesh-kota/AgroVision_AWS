"""
image_preprocess.py — Domain Adaptation Preprocessing
────────────────────────────────────────────────────────────────────────────
The PlantVillage training dataset consists of clean, controlled lab-style photos:
  - Single leaf on plain white/grey background
  - Centered, well-lit, close-up
  - No soil, no other plants, no shadows

Real-world photos (from phone cameras, Google images) have:
  - Natural backgrounds (soil, other plants, sky)
  - Multiple leaves, different angles, shadows
  - JPEG compression artifacts, noise, motion blur

This module applies preprocessing that "normalises" real-world images
to resemble training-set conditions before passing to the CNN model.
This reduces domain shift and significantly improves accuracy on real photos.
"""

import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)


def _find_leaf_region(img_bgr: np.ndarray) -> tuple:
    """
    Find the bounding box of the most leaf-like region in the image.
    Returns (x, y, w, h) of the best candidate region.
    Falls back to full image if no clear leaf region found.
    """
    h, w = img_bgr.shape[:2]
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # --- Strategy 1: GrabCut foreground extraction (best for isolated leaves) ---
    try:
        # Start from a central rect that excludes edges (likely background)
        margin = int(min(h, w) * 0.08)
        rect = (margin, margin, w - 2*margin, h - 2*margin)
        mask = np.zeros((h, w), np.uint8)
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)
        cv2.grabCut(img_bgr, mask, rect, bgd_model, fgd_model, 4, cv2.GC_INIT_WITH_RECT)
        fg_mask = np.where((mask == 2) | (mask == 0), 0, 1).astype(np.uint8)

        # Find largest connected component in foreground
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(fg_mask)
        if num_labels > 1:
            largest = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
            x = stats[largest, cv2.CC_STAT_LEFT]
            y = stats[largest, cv2.CC_STAT_TOP]
            cw = stats[largest, cv2.CC_STAT_WIDTH]
            ch = stats[largest, cv2.CC_STAT_HEIGHT]
            area_frac = (cw * ch) / (w * h)
            # Use only if region is reasonably sized (10-95% of image)
            if 0.10 <= area_frac <= 0.95:
                return (x, y, cw, ch)
    except Exception:
        pass

    # --- Strategy 2: Green/brown colour mask (most leaves are green or diseased brown) ---
    try:
        green_mask = cv2.inRange(hsv,
                                  np.array([25, 30, 30]),
                                  np.array([95, 255, 255]))
        brown_mask = cv2.inRange(hsv,
                                  np.array([8,  40, 40]),
                                  np.array([30, 255, 200]))
        leaf_mask = cv2.bitwise_or(green_mask, brown_mask)

        # Morphological cleanup
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        leaf_mask = cv2.morphologyEx(leaf_mask, cv2.MORPH_CLOSE, kernel)
        leaf_mask = cv2.morphologyEx(leaf_mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(leaf_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest)
            area_frac = area / (w * h)
            if area_frac > 0.08:
                x, y, cw, ch = cv2.boundingRect(largest)
                # Add small padding
                pad = int(min(cw, ch) * 0.05)
                x = max(0, x - pad)
                y = max(0, y - pad)
                cw = min(w - x, cw + 2*pad)
                ch = min(h - y, ch + 2*pad)
                return (x, y, cw, ch)
    except Exception:
        pass

    # Fallback: centre crop 85% of image
    cx, cy = int(w * 0.075), int(h * 0.075)
    return (cx, cy, w - 2*cx, h - 2*cy)


def _enhance_image(img_bgr: np.ndarray) -> np.ndarray:
    """
    Apply CLAHE contrast enhancement to improve visibility of disease symptoms.
    Simulates the high-contrast, well-lit conditions of lab photos.
    """
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l = clahe.apply(l)
    enhanced = cv2.merge([l, a, b])
    return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)


def _remove_background(img_bgr: np.ndarray) -> np.ndarray:
    """
    Attempt background removal by replacing non-leaf pixels with neutral grey.
    This simulates the plain-background training images.
    """
    h, w = img_bgr.shape[:2]
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    green_mask = cv2.inRange(hsv, np.array([25, 25, 25]), np.array([95, 255, 255]))
    brown_mask  = cv2.inRange(hsv, np.array([8,  35, 35]), np.array([30, 255, 200]))
    yellow_mask = cv2.inRange(hsv, np.array([20, 40, 40]), np.array([35, 255, 255]))
    leaf_mask   = cv2.bitwise_or(cv2.bitwise_or(green_mask, brown_mask), yellow_mask)

    # GrabCut for refined foreground
    try:
        margin = int(min(h, w) * 0.06)
        rect   = (margin, margin, w - 2*margin, h - 2*margin)
        gc_mask = np.zeros((h, w), np.uint8)
        bgd = np.zeros((1, 65), np.float64)
        fgd = np.zeros((1, 65), np.float64)
        cv2.grabCut(img_bgr, gc_mask, rect, bgd, fgd, 3, cv2.GC_INIT_WITH_RECT)
        fg = np.where((gc_mask == 2) | (gc_mask == 0), 0, 1).astype(np.uint8) * 255
        # Combine with colour mask
        leaf_mask = cv2.bitwise_or(leaf_mask, fg)
    except Exception:
        pass

    kernel   = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    leaf_mask = cv2.morphologyEx(leaf_mask, cv2.MORPH_CLOSE, kernel)
    leaf_mask = cv2.morphologyEx(leaf_mask, cv2.MORPH_OPEN,  cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    leaf_mask = cv2.GaussianBlur(leaf_mask, (7, 7), 0)

    # Neutral grey background (matches PlantVillage neutral background)
    bg = np.full_like(img_bgr, 200)
    mask3 = np.stack([leaf_mask, leaf_mask, leaf_mask], axis=2).astype(np.float32) / 255.0
    result = (img_bgr.astype(np.float32) * mask3 + bg.astype(np.float32) * (1 - mask3))
    return result.astype(np.uint8)


def preprocess_for_model(image_path: str,
                          target_size: int = 224,
                          remove_bg: bool = True,
                          enhance: bool = True,
                          smart_crop: bool = True) -> np.ndarray:
    """
    Full preprocessing pipeline for a real-world leaf image.

    Steps:
      1. Load image
      2. Smart crop — find and isolate the leaf region
      3. Background removal — replace non-leaf with neutral grey
      4. CLAHE contrast enhancement — improve symptom visibility
      5. Resize to model input size (224×224)

    Returns:
      numpy array (H, W, 3) uint8 in RGB format, ready for preprocess_input()
    """
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        raise ValueError(f"Cannot read image: {image_path}")

    h, w = img_bgr.shape[:2]
    logger.debug(f"Preprocessing {image_path} ({w}×{h})")

    # 1. Smart crop to leaf region
    if smart_crop:
        try:
            x, y, cw, ch = _find_leaf_region(img_bgr)
            img_bgr = img_bgr[y:y+ch, x:x+cw]
        except Exception as e:
            logger.debug(f"Smart crop failed, using full image: {e}")

    # 2. Background removal
    if remove_bg and img_bgr.shape[0] > 50 and img_bgr.shape[1] > 50:
        try:
            img_bgr = _remove_background(img_bgr)
        except Exception as e:
            logger.debug(f"Background removal failed: {e}")

    # 3. CLAHE enhancement
    if enhance:
        try:
            img_bgr = _enhance_image(img_bgr)
        except Exception as e:
            logger.debug(f"Enhancement failed: {e}")

    # 4. Resize to model input
    img_bgr = cv2.resize(img_bgr, (target_size, target_size), interpolation=cv2.INTER_LANCZOS4)

    # 5. Convert to RGB for the model
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    return img_rgb


def is_real_world_image(image_path: str) -> bool:
    """
    Heuristic to detect if an image is a real-world photo vs a lab-style image.
    Real-world images: complex background, multiple colours, natural lighting variation.
    Lab images: uniform background, single centred object, low background variance.
    """
    img = cv2.imread(image_path)
    if img is None:
        return False

    h, w = img.shape[:2]

    # Check background variance (corners of the image)
    corner_size = int(min(h, w) * 0.12)
    corners = [
        img[:corner_size, :corner_size],
        img[:corner_size, w-corner_size:],
        img[h-corner_size:, :corner_size],
        img[h-corner_size:, w-corner_size:],
    ]
    corner_pixels = np.concatenate([c.reshape(-1, 3) for c in corners])
    bg_variance = np.std(corner_pixels.astype(float))

    # High background variance = real-world photo
    return float(bg_variance) > 30.0
