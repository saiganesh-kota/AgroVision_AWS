import logging, os, pickle
import pandas as pd
logger = logging.getLogger(__name__)

BASE       = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE, "models", "fusion_model.pkl")
model      = None

def load_model():
    global model
    if model is None and os.path.exists(MODEL_PATH):
        try:
            model = pickle.load(open(MODEL_PATH, "rb"))
        except Exception as e:
            logger.warning(f"fusion_model load failed: {e}")

def _fallback_risk(temp, humidity, severity, confidence):
    """Heuristic risk when model unavailable."""
    score = 0
    if severity > 50:  score += 2
    elif severity > 25: score += 1
    if humidity > 75:  score += 1
    if temp > 35:      score += 1
    if score >= 3: return "High"
    if score >= 1: return "Medium"
    return "Low"

def predict_risk(temp, humidity, ph, soil_moisture, severity, confidence):
    load_model()
    if model is None:
        return _fallback_risk(temp, humidity, severity, confidence)
    try:
        X = pd.DataFrame([[temp, humidity, ph, soil_moisture, severity, confidence]],
            columns=["temperature","humidity","ph","soil_moisture","severity","confidence"])
        return str(model.predict(X)[0])
    except Exception as e:
        logger.warning(f"predict_risk error: {e}")
        return _fallback_risk(temp, humidity, severity, confidence)

def predict_risk_proba(temp, humidity, ph, soil_moisture, severity, confidence):
    load_model()
    if model is None:
        return [0.3, 0.4, 0.3]
    try:
        X = pd.DataFrame([[temp, humidity, ph, soil_moisture, severity, confidence]],
            columns=["temperature","humidity","ph","soil_moisture","severity","confidence"])
        return model.predict_proba(X)[0]
    except Exception:
        return [0.3, 0.4, 0.3]
