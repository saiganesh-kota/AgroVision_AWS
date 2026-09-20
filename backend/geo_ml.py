import logging
logger = logging.getLogger(__name__)

import os
import pickle
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE, "models", "geo_model.pkl")

model = None

def load_model():
    global model
    if model is None:
        logger.info(f"📦 Loading geo model from: {MODEL_PATH}")
        model = pickle.load(open(MODEL_PATH, "rb"))

def predict_geo(lat, lon, humidity, density=1):
    load_model()
    X = pd.DataFrame(
        [[lat, lon, humidity, density]],
        columns=["lat", "lon", "humidity", "density"]
    )
    return model.predict(X)[0]
