"""
auto_retrain.py
────────────────
Standalone script that watches feedback_data.csv and retrains
recommend_model.pkl whenever enough new feedback rows arrive.

Usage:  python auto_retrain.py          (runs forever)
        python auto_retrain.py --once   (single check and exit)

The retrain_service.py daemon inside Flask handles the recommend_model
via feedback_model. This script provides a CLI alternative when you
want to manually trigger or monitor retraining.
"""
import os
import sys
import time
import pickle
import pandas as pd
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier

BASE          = os.path.dirname(os.path.abspath(__file__))
FEEDBACK_PATH = os.path.join(BASE, "feedback_data.csv")
MODEL_PATH    = os.path.join(BASE, "models", "recommend_model.pkl")
VERSION_DIR   = os.path.join(BASE, "models", "versions")

CHECK_INTERVAL    = 10
RETRAIN_THRESHOLD = 3

os.makedirs(VERSION_DIR, exist_ok=True)

last_trained_rows = 0


def retrain_model(df: pd.DataFrame):
    print(f"[{datetime.now():%H:%M:%S}] 🔥 Retraining recommend_model on {len(df)} rows…")

    df = df.fillna("Unknown")
    if len(df) < 5:
        print("⚠️ Not enough data (need 5+). Skipping.")
        return

    feature_cols = [c for c in ["temperature", "humidity", "ph", "soil_moisture", "severity"] if c in df.columns]
    if "actual" not in df.columns:
        print("⚠️ 'actual' column missing — cannot retrain.")
        return

    X = df[feature_cols]
    y = df["actual"]

    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(X, y)

    # Backup
    if os.path.exists(MODEL_PATH):
        import shutil
        ts     = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = os.path.join(VERSION_DIR, f"recommend_model_{ts}.pkl")
        shutil.copy2(MODEL_PATH, backup)
        print(f"📦 Backed up to {backup}")

    pickle.dump(model, open(MODEL_PATH, "wb"))
    print(f"✅ recommend_model updated at {MODEL_PATH}")


def run_once():
    global last_trained_rows
    if not os.path.exists(FEEDBACK_PATH):
        print("feedback_data.csv not found. Nothing to do.")
        return
    df = pd.read_csv(FEEDBACK_PATH)
    current_rows = len(df)
    print(f"📊 Rows: {current_rows}")
    if current_rows - last_trained_rows >= RETRAIN_THRESHOLD:
        retrain_model(df)
        last_trained_rows = current_rows
    else:
        print(f"No new data (threshold={RETRAIN_THRESHOLD}). Skipping.")


def run_forever():
    global last_trained_rows
    print(f"[{datetime.now():%H:%M:%S}] 🚀 auto_retrain watching {FEEDBACK_PATH}")
    while True:
        try:
            if os.path.exists(FEEDBACK_PATH):
                df = pd.read_csv(FEEDBACK_PATH)
                current_rows = len(df)
                print(f"📊 Current: {current_rows} | Last trained: {last_trained_rows}")
                if current_rows - last_trained_rows >= RETRAIN_THRESHOLD:
                    retrain_model(df)
                    last_trained_rows = current_rows
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    if "--once" in sys.argv:
        run_once()
    else:
        run_forever()
