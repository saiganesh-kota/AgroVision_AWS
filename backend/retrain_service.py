"""
retrain_service.py
───────────────────
Background thread that monitors feedback_data.csv and automatically
retrains the feedback_model.pkl when enough new feedback rows arrive.

Started by app.py on Flask startup — runs as a daemon thread.
"""
import os
import time
import threading
import logging
from datetime import datetime

BASE          = os.path.dirname(os.path.abspath(__file__))
FEEDBACK_PATH = os.path.join(BASE, "feedback_data.csv")
LOG_FILE      = os.path.join(BASE, "retrain.log")

CHECK_INTERVAL   = 30   # seconds between checks
MIN_ROWS         = 5    # minimum rows before first train
RETRAIN_THRESHOLD = 3   # retrain after every +N new rows

logger = logging.getLogger("retrain_service")


def _log(msg: str):
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    logger.info(msg)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _do_retrain():
    """Run retrain_feedback logic inline (avoid subprocess overhead)."""
    try:
        import pandas as pd
        import pickle
        import shutil
        from sklearn.ensemble import RandomForestClassifier

        if not os.path.exists(FEEDBACK_PATH):
            return

        df = pd.read_csv(FEEDBACK_PATH)
        REQUIRED = ["temperature", "humidity", "ph", "soil_moisture", "severity", "actual"]
        available = [c for c in REQUIRED if c in df.columns]
        df = df[available].dropna()

        if len(df) < MIN_ROWS:
            _log(f"⚠️ Only {len(df)} clean rows — need {MIN_ROWS}. Skipping.")
            return

        feature_cols = [c for c in REQUIRED if c != "actual" and c in df.columns]
        X = df[feature_cols]
        y = df["actual"]

        model = RandomForestClassifier(n_estimators=200, random_state=42)
        model.fit(X, y)

        MODEL_PATH  = os.path.join(BASE, "models", "feedback_model.pkl")
        VERSION_DIR = os.path.join(BASE, "models", "versions")
        os.makedirs(VERSION_DIR, exist_ok=True)

        if os.path.exists(MODEL_PATH):
            ts     = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup = os.path.join(VERSION_DIR, f"feedback_model_{ts}.pkl")
            shutil.copy2(MODEL_PATH, backup)

        pickle.dump(model, open(MODEL_PATH, "wb"))
        _log(f"✅ Auto-retrain complete on {len(df)} rows.")

    except Exception as e:
        _log(f"❌ Retrain error: {e}")


def _monitor_loop():
    last_trained_rows = -1
    _log("🚀 Auto-retrain service started")

    while True:
        try:
            if os.path.exists(FEEDBACK_PATH):
                import pandas as pd
                df = pd.read_csv(FEEDBACK_PATH)
                current_rows = len(df)
                _log(f"📊 feedback rows: {current_rows} | last trained at: {last_trained_rows}")

                should_train = (
                    current_rows >= MIN_ROWS and
                    (last_trained_rows == -1 or current_rows - last_trained_rows >= RETRAIN_THRESHOLD)
                )

                if should_train:
                    _do_retrain()
                    last_trained_rows = current_rows
        except Exception as e:
            _log(f"❌ Monitor error: {e}")

        time.sleep(CHECK_INTERVAL)


def start_background_service():
    """Call this from app.py once on startup."""
    t = threading.Thread(target=_monitor_loop, daemon=True, name="retrain-service")
    t.start()
    logger.info("Retrain service thread started.")
    return t


if __name__ == "__main__":
    # Also runnable standalone
    _monitor_loop()
