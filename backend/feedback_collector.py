import logging
logger = logging.getLogger(__name__)


import os
import pandas as pd
from rl_engine import update_q, get_state

BASE = os.path.dirname(os.path.abspath(__file__))
FEEDBACK_PATH = os.path.join(BASE, "feedback_data.csv")

def save_feedback(temp, humidity, ph, soil_moisture, severity, risk, predicted, actual):

    # Save CSV
    data = {
        "temperature": temp,
        "humidity": humidity,
        "ph": ph,
        "soil_moisture": soil_moisture,
        "severity": severity,
        "risk": risk,
        "prediction": predicted,
        "actual": actual
    }

    df = pd.DataFrame([data])

    if os.path.exists(FEEDBACK_PATH):
        df.to_csv(FEEDBACK_PATH, mode='a', header=False, index=False)
    else:
        df.to_csv(FEEDBACK_PATH, index=False)
    # ===============================
    # RL UPDATE
    # ===============================
    state = get_state(humidity, severity, risk)

    reward = 1 if predicted == actual else -1

    update_q(state, predicted, reward)
