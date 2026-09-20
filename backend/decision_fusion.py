import os
import json

BASE = os.path.dirname(os.path.abspath(__file__))
Q_TABLE_PATH = os.path.join(BASE, "q_table.json")

ALPHA = 0.3  # RL influence weight


def load_q_table():
    if os.path.exists(Q_TABLE_PATH):
        try:
            with open(Q_TABLE_PATH) as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def fuse_scores(actions, base_scores, state):
    """
    Fuse ML base_scores with RL Q-values for given state.
    Returns final fused scores dict.
    """
    q_table = load_q_table()
    q_values = q_table.get(state, {a: 0.0 for a in actions})

    # Normalize Q-values
    q_max = max(abs(v) for v in q_values.values()) or 1.0
    q_norm = {a: v / q_max for a, v in q_values.items()}

    fused = {}
    for action in actions:
        ml_score = base_scores.get(action, 0.0)
        rl_boost = q_norm.get(action, 0.0) * ALPHA
        fused[action] = ml_score + rl_boost

    return fused
