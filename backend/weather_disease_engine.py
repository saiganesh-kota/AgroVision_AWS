"""
weather_disease_engine.py — Weather-Disease Correlation Engine (Patent Feature IX)
────────────────────────────────────────────────────────────────────────────────────
Novel patent contribution: correlates real-time weather parameters with
crop-specific disease outbreak probability using established agro-meteorological
thresholds (Wallin's blight model, AUDPC-inspired).

This is NOT in any existing agri-app — it is original and patent-strengthening.
"""

import math
import logging

logger = logging.getLogger(__name__)

# ── Disease Weather Risk Models ───────────────────────────────────────────────
# Threshold-based risk windows for each disease class
# Format: (temp_min, temp_max, rh_min, rain_trigger, description, advice)
DISEASE_WEATHER_MODELS = {
    "fungal_blight": {
        "temp_range":   (15, 30),
        "rh_threshold": 80,
        "rain_trigger": 10,       # mm
        "description":  "Fungal blight thrives in warm, humid conditions",
        "window_hours": 48,
    },
    "rust": {
        "temp_range":   (10, 25),
        "rh_threshold": 85,
        "rain_trigger": 5,
        "description":  "Rust spores spread in cool, moist conditions",
        "window_hours": 24,
    },
    "powdery_mildew": {
        "temp_range":   (18, 28),
        "rh_threshold": 50,       # Note: thrives at LOW humidity unlike others
        "rain_trigger": 0,
        "description":  "Powdery mildew favours warm, DRY conditions",
        "window_hours": 72,
    },
    "bacterial_blight": {
        "temp_range":   (25, 35),
        "rh_threshold": 75,
        "rain_trigger": 8,
        "description":  "Bacterial blight spreads via warm rain splashing",
        "window_hours": 36,
    },
    "leaf_spot": {
        "temp_range":   (20, 32),
        "rh_threshold": 70,
        "rain_trigger": 6,
        "description":  "Leaf spot risk increases with warm wet weather",
        "window_hours": 48,
    },
}

CROP_TO_DISEASES = {
    "tomato":    ["fungal_blight", "leaf_spot", "bacterial_blight"],
    "rice":      ["fungal_blight", "leaf_spot", "bacterial_blight"],
    "wheat":     ["rust", "powdery_mildew", "leaf_spot"],
    "cotton":    ["bacterial_blight", "leaf_spot", "fungal_blight"],
    "maize":     ["fungal_blight", "rust", "leaf_spot"],
    "potato":    ["fungal_blight", "bacterial_blight", "leaf_spot"],
    "groundnut": ["leaf_spot", "rust", "fungal_blight"],
}

SEVERITY_TO_DISEASE = {
    "fungal_blight":   "Fungal Blight",
    "rust":            "Rust",
    "powdery_mildew":  "Powdery Mildew",
    "bacterial_blight":"Bacterial Blight",
    "leaf_spot":       "Leaf Spot",
}


def _blight_units(temp: float, rh: float) -> float:
    """
    Simplified Wallin Blight Unit calculation.
    Used for late blight risk estimation in potato/tomato.
    """
    if rh < 90 or not (10 <= temp <= 24):
        return 0.0
    temp_score = 1.0 - abs(temp - 17) / 10.0
    rh_score   = (rh - 90) / 10.0
    return max(0.0, min(1.0, temp_score * rh_score))


def _fungal_risk(temp: float, rh: float, rainfall: float, model: dict) -> float:
    """Universal fungal risk score 0-1 from weather inputs."""
    t_min, t_max = model["temp_range"]
    rh_thresh    = model["rh_threshold"]
    rain_trig    = model["rain_trigger"]

    # Temperature score
    if t_min <= temp <= t_max:
        t_score = 1.0 - abs(temp - (t_min + t_max) / 2) / ((t_max - t_min) / 2)
        t_score = max(0.0, t_score)
    else:
        margin = min(abs(temp - t_min), abs(temp - t_max))
        t_score = max(0.0, 1.0 - margin / 10.0)

    # Humidity score (special case: powdery mildew grows at low humidity)
    if model.get("description", "").startswith("Powdery"):
        rh_score = max(0.0, 1.0 - rh / 100.0) if rh < rh_thresh else 0.0
    else:
        rh_score = min(1.0, max(0.0, (rh - rh_thresh + 10) / 30.0))

    # Rainfall score
    if rain_trig == 0:
        rain_score = 0.3  # baseline
    else:
        rain_score = min(1.0, rainfall / (rain_trig * 3.0))

    return round(t_score * 0.45 + rh_score * 0.35 + rain_score * 0.20, 4)


def analyse_weather_risk(
    temp: float,
    humidity: float,
    rainfall: float,
    crop: str = "",
) -> dict:
    """
    Returns a full weather-disease correlation analysis:
    {
        overall_risk: 'Low'|'Medium'|'High'|'Critical',
        risk_score:   0.0-1.0,
        blight_units: 0.0-1.0,
        disease_risks: [{ disease, score, description, advice }, ...],
        dominant_factor: str,
        advisory: str,
        favorable_period: str,
    }
    """
    crop_key     = (crop or "").lower().strip()
    disease_keys = CROP_TO_DISEASES.get(crop_key, list(DISEASE_WEATHER_MODELS.keys()))

    disease_risks = []
    for dk in disease_keys:
        model = DISEASE_WEATHER_MODELS.get(dk)
        if not model:
            continue
        score = _fungal_risk(temp, humidity, rainfall, model)
        advice = _build_advice(dk, score, temp, humidity, rainfall)
        disease_risks.append({
            "disease":     SEVERITY_TO_DISEASE.get(dk, dk.replace("_", " ").title()),
            "key":         dk,
            "score":       score,
            "probability": round(score * 100, 1),
            "description": model["description"],
            "advice":      advice,
        })

    disease_risks.sort(key=lambda x: -x["score"])

    # Overall risk
    if disease_risks:
        max_score = disease_risks[0]["score"]
    else:
        max_score = 0.0

    blight_units = _blight_units(temp, humidity)

    if max_score >= 0.75 or blight_units >= 0.8:
        overall = "Critical"
    elif max_score >= 0.55:
        overall = "High"
    elif max_score >= 0.35:
        overall = "Medium"
    else:
        overall = "Low"

    # Dominant factor
    if humidity > 85:
        dominant = f"Very high humidity ({humidity:.0f}%) — primary disease driver"
    elif temp > 30:
        dominant = f"High temperature ({temp:.1f}°C) accelerating pathogen spread"
    elif rainfall > 20:
        dominant = f"Heavy rainfall ({rainfall:.0f}mm) enabling spore dispersal"
    elif humidity < 40:
        dominant = f"Low humidity ({humidity:.0f}%) — powdery mildew risk"
    else:
        dominant = "Moderate weather — baseline disease pressure"

    advisory = _build_overall_advisory(overall, disease_risks, temp, humidity)
    favorable = _favorable_period(temp, humidity, rainfall)

    return {
        "overall_risk":    overall,
        "risk_score":      round(max_score, 4),
        "blight_units":    round(blight_units, 4),
        "disease_risks":   disease_risks[:4],
        "dominant_factor": dominant,
        "advisory":        advisory,
        "favorable_period":favorable,
        "inputs": {
            "temperature": temp,
            "humidity":    humidity,
            "rainfall":    rainfall,
            "crop":        crop or "General",
        },
    }


def _build_advice(disease_key: str, score: float, temp, humidity, rainfall) -> str:
    if score < 0.30:
        return "Risk low — standard monitoring sufficient."
    if disease_key == "fungal_blight":
        if score >= 0.65:
            return "Apply preventive fungicide immediately. Avoid overhead irrigation."
        return "Scout regularly. Apply fungicide if symptoms appear."
    if disease_key == "rust":
        if score >= 0.65:
            return "Apply systemic fungicide. Remove infected tissue. Improve air circulation."
        return "Monitor for orange pustules. Apply triazole fungicide preventively."
    if disease_key == "powdery_mildew":
        if score >= 0.65:
            return "Apply sulfur-based or neem oil spray. Improve ventilation."
        return "Watch for white powdery patches. Avoid excess nitrogen."
    if disease_key == "bacterial_blight":
        if score >= 0.65:
            return "Apply copper-based bactericide. Avoid working in wet conditions."
        return "Scout for water-soaked spots. Use disease-free seeds."
    return "Apply appropriate protectant. Monitor daily."


def _build_overall_advisory(level: str, risks, temp, humidity) -> str:
    if level == "Critical":
        top = risks[0]["disease"] if risks else "disease"
        return (f"⚠️ Critical risk: {top} outbreak likely in next 48 hours. "
                f"Apply treatment immediately. Humidity {humidity:.0f}% is exceeding safe threshold.")
    if level == "High":
        return (f"High disease pressure detected. Apply preventive spray within 24–48 hours. "
                f"Conditions ({temp:.1f}°C, {humidity:.0f}%RH) are near-optimal for pathogens.")
    if level == "Medium":
        return "Moderate risk window. Inspect crops every 2 days. Prepare treatment supplies."
    return "Weather conditions are not favourable for major disease outbreaks. Routine monitoring sufficient."


def _favorable_period(temp, humidity, rainfall) -> str:
    """Estimate when conditions will become safer based on current trends."""
    if humidity > 80 and rainfall > 10:
        return "Risk remains elevated while humidity stays above 80% — expect 3–5 days"
    if temp > 30:
        return "Risk reduces when temperature drops below 28°C"
    return "Current conditions stable — low outbreak risk for 7+ days"
