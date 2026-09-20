"""
feedback_predict.py — TreatmentFeedback Model (auto-detects schema)
──────────────────────────────────────────────────────────────────
Predicts treatment effectiveness. Supports TWO model file formats:

  v1 (legacy, what your real models/feedback_model.pkl currently is):
    A raw sklearn classifier pickled directly — pickle.dump(model, f).
    Only knows severity + humidity. Returns a rough 0-1 estimate.

  v2 (bundle format, requires retraining to produce):
    A dict {"model":..., "schema_version":2, "feature_names":[...],
    "class_enc":{...}, "cv_accuracy":...}. Uses 8 features for a much
    more accurate effectiveness prediction.

This auto-detects which one is actually on disk and uses it correctly,
instead of assuming v2 and crashing on a v1 file (or vice versa).
"""
import os, pickle, logging
import pandas as pd

logger     = logging.getLogger(__name__)
BASE       = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE, "models", "feedback_model.pkl")
_bundle    = None


def _load():
    global _bundle
    if _bundle is not None:
        return _bundle

    raw = pickle.load(open(MODEL_PATH, "rb"))

    if isinstance(raw, dict) and "model" in raw:
        # Genuine v2 bundle
        _bundle = raw
        schema = raw.get("schema_version", 2)
        logger.info(f"feedback_model v{schema} bundle loaded — CV acc={raw.get('cv_accuracy', '?')}")
    else:
        # Legacy v1 — a raw sklearn estimator with no wrapper dict at all.
        # Wrap it so the rest of this module can treat both cases uniformly.
        _bundle = {
            "model": raw,
            "schema_version": 1,
            "feature_names": ["severity", "humidity"],
        }
        logger.info("feedback_model is legacy v1 (raw 2-feature model, no bundle wrapper) — using compatibility mode")

    return _bundle


def predict_feedback(temp, humidity, ph=6.5, soil_moisture=50.0, severity=20.0,
                     treatment_applied_enc=0, severity_after=None,
                     soil_class_enc=1, urgency_class_enc=1, days_between_scans=7):
    """
    Returns treatment_effectiveness_score (float 0-1).
    Works whether the on-disk model is the old 2-feature format or the
    new 8-feature bundle format — degrades gracefully either way.
    """
    try:
        b = _load()
    except Exception as e:
        logger.warning(f"feedback_model could not be loaded, using neutral prior: {e}")
        return 0.5

    schema = b.get("schema_version", 1)
    model  = b["model"]

    if schema < 2:
        # Legacy 2-feature model — predict with what it actually knows
        try:
            row = pd.DataFrame([[severity, humidity]], columns=["severity", "humidity"])
            pred = model.predict(row)[0]
            # Legacy model returns 0/1 (binary) — treat 1 as "effective-ish"
            return 0.7 if int(pred) == 1 else 0.4
        except Exception:
            return 0.5  # legacy model incompatible — neutral default

    # v2 bundle — full 8-feature prediction
    if severity_after is None:
        severity_after = severity * 0.7

    feats = b["feature_names"]
    row = pd.DataFrame([{
        "treatment_applied_enc": treatment_applied_enc,
        "severity_before":       severity,
        "severity_after":        severity_after,
        "temperature":           temp,
        "humidity":              humidity,
        "soil_class_enc":        soil_class_enc,
        "urgency_class_enc":     urgency_class_enc,
        "days_between_scans":    days_between_scans,
    }])[feats]

    proba = model.predict_proba(row)[0]
    effectiveness = float(proba[2]) if len(proba) > 2 else float(proba[-1])
    return round(effectiveness, 4)


def predict_treatment_effectiveness(treatment_applied_enc, severity_before, severity_after,
                                     temperature, humidity, soil_class_enc,
                                     urgency_class_enc, days_between_scans):
    """Full 8-feature prediction. Only meaningful when schema_version >= 2."""
    b = _load()
    if b.get("schema_version", 1) < 2:
        return {"effectiveness_label": "Unknown", "effectiveness_score": 0.5, "probabilities": {}}

    feats = b["feature_names"]
    row = pd.DataFrame([{
        "treatment_applied_enc": treatment_applied_enc,
        "severity_before":       severity_before,
        "severity_after":        severity_after,
        "temperature":           temperature,
        "humidity":              humidity,
        "soil_class_enc":        soil_class_enc,
        "urgency_class_enc":     urgency_class_enc,
        "days_between_scans":    days_between_scans,
    }])[feats]
    pred  = b["model"].predict(row)[0]
    proba = b["model"].predict_proba(row)[0]
    return {
        "effectiveness_label": b.get("class_enc", {}).get(int(pred), str(pred)),
        "effectiveness_score": round(float(proba[2]) if len(proba) > 2 else float(proba[-1]), 4),
        "probabilities": {str(i): round(float(p), 4) for i, p in enumerate(proba)},
    }


def adjust_risk(severity, humidity, risk):
    """Legacy compatibility shim."""
    return risk
