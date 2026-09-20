import os

# ===============================
# SINGLE ACTION SIMULATION
# ===============================
def simulate_action(action, severity, risk):

    risk_map = {
        "Low": 0,
        "Medium": 1,
        "High": 2
    }

    reverse_map = {
        0: "Low",
        1: "Medium",
        2: "High"
    }

    risk_num = risk_map.get(risk, 1)

    effects = {
        "fungicide":     {"severity": -20, "risk": -1},
        "bactericide":   {"severity": -18, "risk": -1},   # ← NEW: bacterial diseases
        "soil_fix":      {"severity": -10, "risk": -1},
        "ph_correction": {"severity": -5,  "risk": -1},
        "irrigation":    {"severity": -3,  "risk": -1},
        "monitor":       {"severity": 2,   "risk": 0}
    }

    effect = effects.get(action, {"severity": 0, "risk": 0})

    new_severity = max(0, severity + effect["severity"])
    new_risk_num = min(2, max(0, risk_num + effect["risk"]))

    new_risk = reverse_map[new_risk_num]

    return new_severity, new_risk


# ===============================
# MULTI ACTION SIMULATION (FINAL FIX)
# ===============================
def simulate_all(actions, severity, feedback_score):

    results = {}

    for action in actions:

        new_severity, new_risk = simulate_action(action, severity, "Medium")

        # ✅ REQUIRED KEYS (DO NOT REMOVE)
        future_severity = new_severity
        future_risk = new_risk

        # OPTIONAL extra (safe)
        future_score = future_severity / 100

        # scoring
        score = (
            (100 - new_severity) * 0.5 +
            feedback_score * 0.3 +
            (100 - future_severity) * 0.2
        )

        results[action] = {
            "severity": new_severity,
            "risk": new_risk,
            "future_severity": future_severity,   # REQUIRED
            "future_risk": future_risk,           # REQUIRED
            "future_score": future_score,         # OPTIONAL
            "score": score
        }

    return results
