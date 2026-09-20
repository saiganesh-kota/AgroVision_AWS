import logging
logger = logging.getLogger(__name__)

"""
retrain_feedback.py
────────────────────
Retrains the feedback_model.pkl from the latest feedback_data.csv.
Called automatically by retrain_service.py when enough new rows exist.
Can also be run manually:  python retrain_feedback.py
"""
import os
import pickle
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime

BASE         = os.path.dirname(os.path.abspath(__file__))
FEEDBACK_PATH = os.path.join(BASE, "feedback_data.csv")
MODEL_PATH    = os.path.join(BASE, "models", "feedback_model.pkl")
VERSION_DIR   = os.path.join(BASE, "models", "versions")

os.makedirs(VERSION_DIR, exist_ok=True)

REQUIRED_COLS = ["temperature", "humidity", "ph", "soil_moisture", "severity", "actual"]


def retrain():
    if not os.path.exists(FEEDBACK_PATH):
        raise FileNotFoundError(f"feedback_data.csv not found at {FEEDBACK_PATH}")

    df = pd.read_csv(FEEDBACK_PATH)

    # Keep only rows that have all required columns
    available = [c for c in REQUIRED_COLS if c in df.columns]
    df = df[available].dropna()

    if len(df) < 5:
        raise ValueError(f"Not enough clean feedback rows ({len(df)}). Need at least 5.")

    feature_cols = [c for c in REQUIRED_COLS if c != "actual" and c in df.columns]
    X = df[feature_cols]
    y = df["actual"]

    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X, y)

    # Back up current model before overwriting
    if os.path.exists(MODEL_PATH):
        ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup  = os.path.join(VERSION_DIR, f"feedback_model_{ts}.pkl")
        import shutil
        shutil.copy2(MODEL_PATH, backup)
        logger.info(f"📦 Backup saved: {backup}")

    pickle.dump(model, open(MODEL_PATH, "wb"))
    logger.info(f"✅ feedback_model retrained on {len(df)} rows → {MODEL_PATH}")
    return len(df)


if __name__ == "__main__":
    retrain()
