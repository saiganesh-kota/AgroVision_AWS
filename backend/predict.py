import logging, os, pickle
import pandas as pd
logger = logging.getLogger(__name__)

BASE       = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE, "models", "soil_model.pkl")
model      = None

def load_model():
    global model
    if model is None and os.path.exists(MODEL_PATH):
        try:
            model = pickle.load(open(MODEL_PATH, "rb"))
        except Exception as e:
            logger.warning(f"soil_model load failed: {e}")

def predict_soil(temp, humidity, ph, rainfall):
    load_model()
    soil_moisture = humidity * 0.5 + rainfall * 0.05
    if model is not None:
        try:
            X = pd.DataFrame([[temp, humidity, ph, soil_moisture]],
                columns=["temperature","humidity","ph","soil_moisture"])
            result = str(model.predict(X)[0]).strip().capitalize()
            if result in ("Good","Moderate","Poor"):
                return result
        except Exception as e:
            logger.warning(f"predict_soil error: {e}")
    # Heuristic fallback
    if ph < 5.5 or ph > 7.5:  return "Poor"
    if humidity < 40 or humidity > 80: return "Moderate"
    return "Good"
