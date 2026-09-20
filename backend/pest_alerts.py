"""
pest_alerts.py — Pest & Disease Alert Engine (Patent Feature IX)
─────────────────────────────────────────────────────────────────
Generates context-aware pest/disease alerts based on crop, weather,
season and geo-risk. No extra model needed — rule + data driven.
"""
from datetime import datetime

# ── Crop-specific high-risk pests/diseases ────────────────────────────────────
CROP_THREATS = {
    "Wheat":     [("Rust",           "fungal",   {"humidity":70,"temp_min":15,"temp_max":25}),
                  ("Powdery Mildew", "fungal",   {"humidity":80,"temp_min":15,"temp_max":22}),
                  ("Aphids",         "insect",   {"humidity":60,"temp_min":18,"temp_max":28})],
    "Rice":      [("Blast",          "fungal",   {"humidity":85,"temp_min":25,"temp_max":32}),
                  ("Brown Planthopper","insect", {"humidity":80,"temp_min":22,"temp_max":30}),
                  ("Stem Borer",     "insect",   {"humidity":75,"temp_min":20,"temp_max":30})],
    "Tomato":    [("Early Blight",   "fungal",   {"humidity":75,"temp_min":24,"temp_max":30}),
                  ("Late Blight",    "fungal",   {"humidity":90,"temp_min":10,"temp_max":24}),
                  ("Fruit Borer",    "insect",   {"humidity":65,"temp_min":25,"temp_max":35})],
    "Cotton":    [("Bollworm",       "insect",   {"humidity":60,"temp_min":25,"temp_max":38}),
                  ("Whitefly",       "insect",   {"humidity":55,"temp_min":28,"temp_max":38}),
                  ("Pink Bollworm",  "insect",   {"humidity":60,"temp_min":22,"temp_max":32})],
    "Maize":     [("Fall Armyworm",  "insect",   {"humidity":70,"temp_min":22,"temp_max":30}),
                  ("Corn Smut",      "fungal",   {"humidity":75,"temp_min":26,"temp_max":34}),
                  ("Stem Borer",     "insect",   {"humidity":70,"temp_min":20,"temp_max":30})],
    "Potato":    [("Late Blight",    "fungal",   {"humidity":90,"temp_min":10,"temp_max":24}),
                  ("Early Blight",   "fungal",   {"humidity":80,"temp_min":20,"temp_max":30}),
                  ("Aphids",         "insect",   {"humidity":60,"temp_min":15,"temp_max":25})],
    "Soybean":   [("Rust",           "fungal",   {"humidity":80,"temp_min":18,"temp_max":28}),
                  ("Stem Fly",       "insect",   {"humidity":70,"temp_min":20,"temp_max":30})],
    "Groundnut": [("Leaf Spot",      "fungal",   {"humidity":80,"temp_min":25,"temp_max":35}),
                  ("Thrips",         "insect",   {"humidity":55,"temp_min":25,"temp_max":35})],
    "Chilli":    [("Anthracnose",    "fungal",   {"humidity":85,"temp_min":25,"temp_max":32}),
                  ("Thrips",         "insect",   {"humidity":55,"temp_min":25,"temp_max":35})],
    "Sugarcane": [("Red Rot",        "fungal",   {"humidity":80,"temp_min":25,"temp_max":35}),
                  ("Top Borer",      "insect",   {"humidity":75,"temp_min":22,"temp_max":30})],
}

# Generic fallback threats for unknown crops
GENERIC_THREATS = [
    ("Fungal Leaf Spot", "fungal",  {"humidity":75,"temp_min":20,"temp_max":30}),
    ("Aphids",           "insect",  {"humidity":60,"temp_min":18,"temp_max":28}),
]

PREVENTION = {
    "fungal": [
        "Apply copper-based fungicide as protective spray",
        "Improve field drainage to reduce leaf wetness",
        "Increase plant spacing for better air circulation",
        "Avoid overhead irrigation; use drip system",
    ],
    "insect": [
        "Install yellow sticky traps for early monitoring",
        "Apply neem oil (5ml/L) as organic deterrent",
        "Release natural predators (ladybirds for aphids)",
        "Use recommended insecticide at threshold level",
    ],
    "bacterial": [
        "Remove and destroy infected plant material",
        "Apply copper oxychloride spray",
        "Avoid working in wet fields",
    ],
}


def _month_risk_multiplier() -> float:
    """Kharif (Jun-Oct) and Rabi (Nov-Mar) peak disease windows."""
    m = datetime.now().month
    if m in (7, 8, 9):   return 1.3   # peak monsoon — highest fungal risk
    if m in (6, 10):     return 1.1
    if m in (1, 2, 12):  return 1.15  # rabi rust season
    return 1.0


def generate_pest_alerts(crop: str, temp: float, humidity: float,
                         severity: float, geo_risk: str) -> list[dict]:
    """
    Returns a list of pest/disease alert dicts, each with:
        name, type, risk_level, probability, prevention, is_active
    """
    threats = CROP_THREATS.get(crop, GENERIC_THREATS)
    month_mult = _month_risk_multiplier()
    geo_mult   = {"High": 1.4, "Medium": 1.1, "Low": 0.9}.get(geo_risk, 1.0)
    alerts     = []

    for name, threat_type, conditions in threats:
        # Base probability from weather match
        hum_match  = 1.0 if humidity  >= conditions["humidity"]   else humidity  / conditions["humidity"]
        temp_match = 1.0 if conditions["temp_min"] <= temp <= conditions["temp_max"] else (
            max(0.0, 1.0 - abs(temp - (conditions["temp_min"] + conditions["temp_max"]) / 2) / 10)
        )
        base_prob = hum_match * 0.5 + temp_match * 0.5
        prob      = min(1.0, base_prob * month_mult * geo_mult)

        # Boost if already diseased
        if severity > 20:
            prob = min(1.0, prob * 1.2)

        if prob < 0.25:   risk = "Low"
        elif prob < 0.55: risk = "Medium"
        elif prob < 0.80: risk = "High"
        else:             risk = "Critical"

        alerts.append({
            "name":        name,
            "type":        threat_type,
            "risk_level":  risk,
            "probability": round(prob, 3),
            "prevention":  PREVENTION.get(threat_type, PREVENTION["fungal"])[:2],
            "is_active":   prob >= 0.50,
            "conditions":  f"Risk when humidity >{conditions['humidity']}% & temp {conditions['temp_min']}–{conditions['temp_max']}°C",
        })

    # Sort by probability descending
    alerts.sort(key=lambda x: -x["probability"])
    return alerts
