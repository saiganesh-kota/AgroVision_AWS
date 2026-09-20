import logging, os, pickle
import pandas as pd
logger = logging.getLogger(__name__)

BASE       = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE, "models", "progression_model.pkl")
model      = None

def load_model():
    global model
    if model is None and os.path.exists(MODEL_PATH):
        try:
            model = pickle.load(open(MODEL_PATH, "rb"))
        except Exception as e:
            logger.warning(f"progression_model load failed: {e}")

def _fallback_progression(severity, humidity):
    """Linear progression estimate: severity grows ~0.8%/day if humid."""
    rate = 0.8 if humidity > 65 else 0.4
    return [round(min(severity + i * rate, 100), 2) for i in range(7)]

def predict_future_severity(temp, humidity, ph, soil_moisture, severity):
    load_model()
    if model is None:
        return _fallback_progression(severity, humidity)
    try:
        X = pd.DataFrame([[temp, humidity, ph, soil_moisture, severity]],
            columns=["temperature","humidity","ph","soil_moisture","severity"])
        result = model.predict(X)[0]
        if hasattr(result, "tolist"):    return result.tolist()
        elif isinstance(result, (list, tuple)): return list(result)
        else:
            val = float(result)
            return [round(val + i * 0.5, 2) for i in range(7)]
    except Exception as e:
        logger.warning(f"progression error: {e}")
        return _fallback_progression(severity, humidity)
