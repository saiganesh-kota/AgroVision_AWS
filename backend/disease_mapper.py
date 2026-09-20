"""
disease_mapper.py — Crop-Specific Disease Identification (Patent Feature I)
────────────────────────────────────────────────────────────────────────────
When the ML model is unavailable (CV fallback), uses colour/texture metrics
and crop type to identify the MOST PROBABLE disease name, not just "Diseased".

This gives patent-novel specificity: same image + different crop → different
disease name (because tomato blight ≠ wheat rust ≠ rice blast even if
severity metrics are identical).
"""

import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

# ── Per-crop disease profiles ─────────────────────────────────────────────────
# Each entry: (disease_name, hue_min, hue_max, brown_min, brown_max, description)
# HSV hue range of the SPOT colour characteristic of that disease
CROP_DISEASES = {
    "tomato": [
        ("Early Blight",        10, 25, 0.05, 0.40, "Concentric dark-brown rings on lower leaves"),
        ("Late Blight",          5, 20, 0.10, 0.60, "Water-soaked grey-green lesions turning brown"),
        ("Leaf Mold",           25, 45, 0.03, 0.25, "Yellow patches with olive-green mold underside"),
        ("Septoria Leaf Spot",  12, 28, 0.08, 0.45, "Small circular spots with dark borders"),
    ],
    "rice": [
        ("Blast",               10, 25, 0.08, 0.50, "Diamond-shaped grey lesions with brown borders"),
        ("Brown Spot",          15, 30, 0.10, 0.55, "Oval brown spots with yellow halos"),
        ("Sheath Blight",       20, 35, 0.05, 0.35, "Oval lesions on sheath with grey-white centre"),
        ("Bacterial Blight",    25, 45, 0.02, 0.20, "Yellow to white lesions along leaf margins"),
    ],
    "wheat": [
        ("Rust (Yellow)",       22, 40, 0.03, 0.20, "Yellow-orange stripe pustules along leaf veins"),
        ("Rust (Brown)",        10, 22, 0.08, 0.45, "Small round orange-brown pustules"),
        ("Powdery Mildew",      30, 50, 0.01, 0.15, "White powdery coating on upper leaf surface"),
        ("Septoria Blotch",     15, 28, 0.10, 0.50, "Irregular tan blotches with yellow halos"),
    ],
    "cotton": [
        ("Alternaria Leaf Spot", 15, 30, 0.08, 0.50, "Circular brown spots with concentric rings"),
        ("Bacterial Blight",    20, 35, 0.05, 0.30, "Angular water-soaked spots turning brown"),
        ("Leaf Curl Virus",     25, 45, 0.03, 0.20, "Upward curling with vein swelling"),
        ("Grey Mildew",         28, 50, 0.02, 0.18, "Circular grey-white spots on leaves"),
    ],
    "maize": [
        ("Northern Leaf Blight", 10, 25, 0.08, 0.45, "Long elliptical grey-green lesions"),
        ("Common Rust",          12, 22, 0.10, 0.55, "Circular to elongated brown pustules"),
        ("Gray Leaf Spot",       18, 32, 0.06, 0.40, "Rectangular grey lesions between veins"),
        ("Downy Mildew",         25, 45, 0.03, 0.22, "Pale green to yellow streaking"),
    ],
    "potato": [
        ("Late Blight",          8, 20, 0.10, 0.60, "Dark water-soaked lesions, white mold below"),
        ("Early Blight",        12, 25, 0.08, 0.45, "Dark-brown rings in concentric pattern"),
        ("Mosaic Virus",        25, 45, 0.02, 0.15, "Light-dark green mosaic mottling"),
        ("Common Scab",         10, 22, 0.15, 0.65, "Rough corky spots on surface"),
    ],
    "groundnut": [
        ("Early Leaf Spot",     10, 25, 0.06, 0.40, "Brown circular spots with yellow halos"),
        ("Late Leaf Spot",      15, 30, 0.10, 0.55, "Dark brown to black circular lesions"),
        ("Rust",                12, 22, 0.08, 0.50, "Small orange-brown pustules"),
        ("Collar Rot",          20, 35, 0.12, 0.60, "Dark water-soaked collar region"),
    ],
}

# Generic fallback diseases used when crop is unknown
GENERIC_DISEASES = [
    ("Fungal Leaf Blight",  10, 28, 0.08, 0.50, "Brown necrotic lesions with yellow margins"),
    ("Bacterial Leaf Spot", 20, 40, 0.05, 0.30, "Water-soaked angular spots turning brown"),
    ("Nutrient Deficiency", 25, 50, 0.02, 0.20, "Interveinal chlorosis, yellowing pattern"),
    ("Powdery Mildew",      30, 55, 0.01, 0.15, "White powdery coating on leaf surface"),
]


def identify_disease(image_path: str, crop: str, severity: float) -> dict:
    """
    Returns { disease, description, confidence, method }.
    Always returns something — never raises.
    """
    if severity < 3.0:
        return {
            "disease":     "Healthy",
            "description": "No significant disease symptoms detected.",
            "confidence":  90.0,
            "method":      "severity_threshold",
        }

    img = cv2.imread(image_path)
    if img is None:
        return _fallback_response(crop, severity)

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    rgb = cv2.resize(rgb, (224, 224))
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)

    # Measure brown/yellow spot characteristics
    brown_mask  = cv2.inRange(hsv, np.array([10, 40, 40]), np.array([35, 255, 255]))
    brown_ratio = float(np.sum(brown_mask > 0)) / brown_mask.size

    # Mean hue of disease-spot pixels
    spot_hues = hsv[:, :, 0][brown_mask > 0]
    mean_hue  = float(np.mean(spot_hues)) if len(spot_hues) > 0 else 20.0

    # Look up crop-specific diseases
    crop_key    = (crop or "").lower().strip()
    disease_list = CROP_DISEASES.get(crop_key, GENERIC_DISEASES)

    best_name  = None
    best_desc  = None
    best_score = -1.0

    for entry in disease_list:
        name, h_min, h_max, b_min, b_max, desc = entry

        # Score: 1 if hue in range, 0 otherwise (partial for near-range)
        hue_score = 0.0
        if h_min <= mean_hue <= h_max:
            hue_score = 1.0
        elif mean_hue < h_min:
            hue_score = max(0.0, 1.0 - (h_min - mean_hue) / 15.0)
        else:
            hue_score = max(0.0, 1.0 - (mean_hue - h_max) / 15.0)

        # Score: how well brown_ratio fits expected range
        br_score = 0.0
        if b_min <= brown_ratio <= b_max:
            br_score = 1.0
        elif brown_ratio < b_min:
            br_score = max(0.0, 1.0 - (b_min - brown_ratio) / 0.15)
        else:
            br_score = max(0.0, 1.0 - (brown_ratio - b_max) / 0.20)

        score = hue_score * 0.55 + br_score * 0.45
        if score > best_score:
            best_score = score
            best_name  = name
            best_desc  = desc

    if best_name is None:
        return _fallback_response(crop, severity)

    # Confidence: blend match score with severity signal
    conf = round(min(40.0 + best_score * 40.0 + (severity / 100.0) * 20.0, 88.0), 1)

    return {
        "disease":     best_name,
        "description": best_desc,
        "confidence":  conf,
        "method":      "cv_colour_analysis",
    }


def _fallback_response(crop: str, severity: float) -> dict:
    if severity > 40:
        return {"disease": "Severe Leaf Disease",    "description": "Extensive damage detected.", "confidence": 55.0, "method": "heuristic"}
    if severity > 15:
        return {"disease": "Moderate Leaf Infection","description": "Moderate infection symptoms.", "confidence": 50.0, "method": "heuristic"}
    return {"disease": "Minor Leaf Stress",          "description": "Early-stage stress symptoms.", "confidence": 45.0, "method": "heuristic"}
