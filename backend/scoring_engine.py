"""
scoring_engine.py — Farm Health Score Calculator (Patent Feature I)
────────────────────────────────────────────────────────────────────
Produces a 0-100 farm health index from diagnosis + environment inputs.
Also provides a per-component breakdown for the frontend health panel.
"""
import logging

logger = logging.getLogger(__name__)


def _soil_score(soil) -> float:
    """Map soil string or dict to 0-100 score."""
    if isinstance(soil, dict):
        label = str(soil.get("condition", soil.get("label", "Moderate")))
    else:
        label = str(soil).strip().capitalize()
    return {"Good": 90.0, "Moderate": 62.0, "Poor": 35.0}.get(label, 62.0)


def _humidity_penalty(humidity: float) -> float:
    """Deviation from ideal 45-65% band → 0-40 penalty."""
    h = float(humidity)
    if 45 <= h <= 65:
        return 0.0
    elif h < 45:
        return min((45 - h) * 1.1, 40.0)
    else:
        return min((h - 65) * 1.1, 40.0)


def calculate_health_score(crop, severity, soil, humidity, confidence) -> float:
    """
    Composite health score (0-100):
      40% leaf health  (inverse severity)
      20% model confidence
      20% soil condition
      20% environmental stress
    """
    leaf_health  = max(0.0, 100.0 - float(severity))
    conf_score   = min(float(confidence), 100.0)
    soil_sc      = _soil_score(soil)
    env_health   = max(0.0, 100.0 - _humidity_penalty(humidity))

    score = (
        0.40 * leaf_health  +
        0.20 * conf_score   +
        0.20 * soil_sc      +
        0.20 * env_health
    )
    return round(max(0.0, min(100.0, score)), 2)


def health_breakdown(crop, severity, soil, humidity, confidence) -> list[dict]:
    """
    Returns per-component breakdown for frontend:
        [{ component, score (0-100), weight, label }, ...]
    """
    leaf  = max(0.0, 100.0 - float(severity))
    conf  = min(float(confidence), 100.0)
    soil_ = _soil_score(soil)
    env   = max(0.0, 100.0 - _humidity_penalty(humidity))

    def grade(v):
        if v >= 80: return "Excellent"
        if v >= 60: return "Good"
        if v >= 40: return "Fair"
        return "Poor"

    return [
        {"component": "Leaf Health",       "score": round(leaf,  2), "weight": 40, "label": grade(leaf)},
        {"component": "Model Confidence",  "score": round(conf,  2), "weight": 20, "label": grade(conf)},
        {"component": "Soil Condition",    "score": round(soil_, 2), "weight": 20, "label": grade(soil_)},
        {"component": "Environment",       "score": round(env,   2), "weight": 20, "label": grade(env)},
    ]
