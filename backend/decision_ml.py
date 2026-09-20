import logging, os, pickle
import pandas as pd
logger = logging.getLogger(__name__)

BASE       = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE, "models", "decision_model.pkl")
model      = None

def load_model():
    global model
    if model is None and os.path.exists(MODEL_PATH):
        try:
            model = pickle.load(open(MODEL_PATH, "rb"))
        except Exception as e:
            logger.warning(f"decision_model load failed: {e}")

def _fallback_decision(severity, confidence):
    if severity > 50:  return "immediate_action"
    if severity > 20:  return "monitor_closely"
    return "routine_care"

def predict_decision(temp, humidity, ph, soil_moisture, severity, confidence):
    load_model()
    if model is None:
        return _fallback_decision(severity, confidence)
    try:
        X = pd.DataFrame([[temp, humidity, ph, soil_moisture, severity, confidence]],
            columns=["temperature","humidity","ph","soil_moisture","severity","confidence"])
        return str(model.predict(X)[0])
    except Exception as e:
        logger.warning(f"predict_decision error: {e}")
        return _fallback_decision(severity, confidence)
