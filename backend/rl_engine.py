"""
rl_engine.py — RL Policy Layer (Schema v2)
───────────────────────────────────────────
State encoding: u{urgency_class}_d{disease_band}_s{soil_class}
48 states — all components derived from trained model outputs.
No raw sensor values appear in any state key.
"""
import os, json, random, logging

logger       = logging.getLogger(__name__)
BASE         = os.path.dirname(os.path.abspath(__file__))
Q_TABLE_PATH = os.path.join(BASE, "q_table.json")
CN_PATH      = os.path.join(BASE, "models", "class_names.json")

# Self-heal: generate actions_config.json (and the other shared configs)
# from disease_treatments.py if it doesn't exist yet, instead of crashing
# at import time. Single source of truth — see disease_treatments.py.
try:
    from disease_treatments import ensure_configs_exist
    ensure_configs_exist(BASE)
except Exception as _e:
    logger.warning(f"Could not self-heal configs from disease_treatments.py: {_e}")

def _load_actions():
    with open(os.path.join(BASE,"actions_config.json")) as f:
        return json.load(f)["actions"]

def _load_rl_params():
    with open(os.path.join(BASE,"actions_config.json")) as f:
        cfg = json.load(f)
    p = cfg.get("rl_hyperparams", {})
    return p.get("epsilon",0.20), p.get("alpha",0.12), p.get("gamma",0.85)

def _load_disease_bands():
    cn = json.load(open(CN_PATH))
    return {int(k): int(v) for k,v in cn.get("disease_bands",{}).items()}

ACTIONS        = _load_actions()
EPSILON, ALPHA, GAMMA = _load_rl_params()
DISEASE_BANDS  = _load_disease_bands()

def _load_q():
    if os.path.exists(Q_TABLE_PATH):
        try:
            data = json.load(open(Q_TABLE_PATH))
            # Support both v1 flat format and v2 nested format
            if isinstance(data, dict) and "q_values" in data:
                return data  # v2
            # Legacy v1 — wrap
            return {"schema_version":1,"q_values":data,"visit_counts":{},
                    "total_updates":0,"last_updated":""}
        except Exception:
            pass
    return {"schema_version":2,"q_values":{},"visit_counts":{},"total_updates":0}

def _save_q(qt):
    import json as _j
    from datetime import datetime
    qt["last_updated"] = datetime.now().isoformat()
    with open(Q_TABLE_PATH,"w") as f:
        _j.dump(qt, f, indent=2)

def get_state(urgency_class_enc: int, disease_class_id: int, soil_class_enc: int) -> str:
    """
    Encode RL state from trained model outputs only.
    urgency_class_enc : 0–3 from MetaFusion
    disease_class_id  : 0–19 from class_names.json
    soil_class_enc    : 0–2 from soil_model.pkl
    Returns: "u{u}_d{d}_s{s}"
    """
    u = max(0, min(3, int(urgency_class_enc)))
    d = DISEASE_BANDS.get(int(disease_class_id), 1)
    s = max(0, min(2, int(soil_class_enc)))
    return f"u{u}_d{d}_s{s}"

def _get_state_epsilon(qt, state):
    """Per-state epsilon: decays as visits accumulate."""
    vc  = qt.get("visit_counts",{}).get(state,{})
    total_visits = sum(vc.values()) if vc else 0
    return max(0.05, EPSILON / (1 + total_visits * 0.02))

def choose_action(state: str) -> str:
    qt = _load_q()
    qv = qt["q_values"]
    if state not in qv:
        qv[state] = {a: 0.0 for a in ACTIONS}
        qt.setdefault("visit_counts",{})[state] = {a:0 for a in ACTIONS}
        _save_q(qt)

    eps = _get_state_epsilon(qt, state)
    if random.random() < eps:
        return random.choice(ACTIONS)

    qs   = qv[state]
    best = max(qs.values())
    return random.choice([a for a,v in qs.items() if v == best])

def compute_reward(old_sev: float, new_sev: float,
                   old_risk: str, new_risk: str,
                   effectiveness_score: float = None) -> float:
    """
    Reward = observed effectiveness (if available) or simulated severity reduction.
    effectiveness_score from TreatmentFeedback model (0–1) takes priority.
    """
    if effectiveness_score is not None:
        return round(effectiveness_score * 20.0, 4)
    risk_map = {"Low":0,"Medium":1,"High":2}
    sev_gain  = float(old_sev - new_sev)
    risk_gain = (risk_map.get(str(old_risk).capitalize(),1) -
                 risk_map.get(str(new_risk).capitalize(),1)) * 10.0
    return round(sev_gain + risk_gain, 4)

def update_q(state: str, action: str, reward: float,
             next_state: str = None, reward_type: str = "simulated") -> None:
    qt = _load_q()
    qv = qt.setdefault("q_values",{})
    vc = qt.setdefault("visit_counts",{})

    if state not in qv:
        qv[state] = {a: 0.0 for a in ACTIONS}
    if state not in vc:
        vc[state] = {a: 0 for a in ACTIONS}

    current = qv[state].get(action, 0.0)
    future  = GAMMA * max(qv[next_state].values()) if next_state and next_state in qv else 0.0
    qv[state][action] = round(current + ALPHA*(reward + future - current), 6)
    vc[state][action] = vc[state].get(action,0) + 1
    qt["total_updates"] = qt.get("total_updates",0) + 1
    _save_q(qt)

# Legacy shim so old callers using get_state(humidity, severity, risk) still work
def get_state_legacy(humidity: float, severity: float, risk) -> str:
    h = int(min(humidity,99)/10)
    s = int(min(severity,99)/10)
    r = str(risk).strip().capitalize()
    if r not in ("Low","Medium","High"): r = "Medium"
    return f"h{h}_s{s}_r{r}"
