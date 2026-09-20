import logging
logger = logging.getLogger(__name__)

import os
import json
import pickle
import pandas as pd

# Module-level cache for class_names.json reverse-lookup.
# _get_disease_class_id() was previously re-reading and re-parsing this
# JSON file on every single prediction call — unnecessary disk I/O for
# a file that never changes between requests.
_CN_LABEL_TO_IDX: dict | None = None  # {label_str: int_index}

from feedback_predict import predict_feedback
from action_simulator import simulate_all
from confidence_calibrator import calibrate_confidence
from disease_treatments import (
    get_valid_actions, get_treatment_detail, get_cultural_practices,
    get_pathogen_info, ACTION_TYPE, ACTION_COST_INR, TREATMENT_DISPLAY_NAME,
    ALL_ACTIONS, get_crop_valid_actions, get_crop_treatment,
    get_crop_cultural_practices, PATHOGEN_ENC, CROP_ENC, CROP_NAME_ALIASES,
)

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE, "models", "recommend_model.pkl")
WEIGHTS_PATH = os.path.join(BASE, "adaptive_weights.json")

model = None


# ===============================
# LOAD MODEL
# ===============================
def load_model():
    global model
    if model is None and os.path.exists(MODEL_PATH):
        try:
            model = pickle.load(open(MODEL_PATH, "rb"))
            logger.info(f"recommend_model loaded: {model.n_features_in_} features, classes={list(model.classes_)}")
        except Exception as e:
            logger.warning(f"recommend_model load failed: {e}")


def _get_disease_class_id(disease_class: str) -> int:
    """Look up numeric id for disease_class label from class_names.json.
    Result is O(1) after first call — the JSON is parsed once and cached."""
    global _CN_LABEL_TO_IDX
    if not disease_class:
        return -1
    if _CN_LABEL_TO_IDX is None:
        cn_path = os.path.join(BASE, "models", "class_names.json")
        if not os.path.exists(cn_path):
            _CN_LABEL_TO_IDX = {}
        else:
            try:
                raw = json.load(open(cn_path))
                _CN_LABEL_TO_IDX = {
                    v: int(k) for k, v in raw.items() if k != "disease_bands"
                }
            except Exception as e:
                logger.warning("Failed to cache class_names.json: %s", e)
                _CN_LABEL_TO_IDX = {}
    return _CN_LABEL_TO_IDX.get(disease_class, -1)


def _get_crop_enc(crop_type: str) -> int:
    """Encode crop name to integer for model input."""
    if not crop_type:
        return -1
    key = crop_type.strip().lower()
    key = CROP_NAME_ALIASES.get(key, key)
    return CROP_ENC.get(key, -1)


def _get_pathogen_enc(pathogen_type: str) -> int:
    return PATHOGEN_ENC.get((pathogen_type or "unknown").strip().lower(), 1)


# ===============================
# LOAD WEIGHTS  (auto-heals if a new action like 'bactericide' is added later)
# ===============================
def load_weights():
    weights = {}
    if os.path.exists(WEIGHTS_PATH):
        try:
            with open(WEIGHTS_PATH, "r") as f:
                weights = json.load(f)
        except Exception:
            weights = {}

    # Ensure every known action has a weight entry (forward-compatible)
    changed = False
    for action in ALL_ACTIONS:
        if action not in weights:
            weights[action] = 0.5
            changed = True

    if changed:
        save_weights(weights)

    return weights


# ===============================
# SAVE WEIGHTS
# ===============================
def save_weights(weights):
    with open(WEIGHTS_PATH, "w") as f:
        json.dump(weights, f)


# ===============================
# MAIN RECOMMENDATION ENGINE
# ===============================
def predict_recommendation(temp, humidity, ph, soil_moisture, severity, confidence,
                            disease_class: str = None, crop_type: str = None):
    """
    disease_class: exact label from class_names.json, e.g. 'Tomato___Bacterial_spot'.
                   Optional — when not provided (binary model / CV fallback),
                   falls back to the full general action set as before.

    ARCHITECTURE NOTE (patent-relevant):
      disease_class only narrows the CANDIDATE action set to what is
      biologically valid for that pathogen (domain knowledge constraint —
      e.g. a bacterial infection cannot be treated with fungicide).
      The actual choice among valid candidates is still computed by the
      ML model + RL fusion + adaptive weights exactly as before — nothing
      about the decision-making itself is hardcoded.
    """

    load_model()

    # -------------------------------
    # DISEASE-CONSTRAINED ACTION SPACE
    # Priority: specific disease class > crop-level fallback > all actions
    # -------------------------------
    if disease_class:
        valid_actions = get_valid_actions(disease_class)
        pathogen_info = get_pathogen_info(disease_class)
    elif crop_type:
        # Use crop-level knowledge when model can't identify specific disease
        valid_actions = get_crop_valid_actions(crop_type)
        pathogen_info = {"pathogen_type": "unknown", "pathogen": f"Common {crop_type} pathogen"}
    else:
        valid_actions = ALL_ACTIONS
        pathogen_info = {}

    # -------------------------------
    # INPUT PREP
    # -------------------------------
    confidence = calibrate_confidence(confidence)

    # Build feature vector for new 10-feature model
    disease_class_id  = _get_disease_class_id(disease_class)
    crop_type_id      = _get_crop_enc(crop_type)
    pathogen_type_enc = _get_pathogen_enc(pathogen_info.get("pathogen_type", "unknown"))
    # Compute urgency_class from severity (0=healthy, 1=low, 2=moderate, 3=high, 4=critical)
    urgency_class_enc = 0 if severity < 5 else (1 if severity < 20 else (2 if severity < 40 else (3 if severity < 65 else 4)))

    if model is None:
        # Heuristic fallback — same logic as model, just rule-based
        if "bactericide" in valid_actions and pathogen_info.get("pathogen_type") == "bacterial":
            base_prediction = "bactericide"
        elif severity > 40 and "fungicide" in valid_actions:
            base_prediction = "fungicide"
        elif ph < 5.8 and "ph_correction" in valid_actions:
            base_prediction = "ph_correction"
        elif humidity < 40 and "irrigation" in valid_actions:
            base_prediction = "irrigation"
        else:
            base_prediction = "monitor"
    else:
        try:
            # Try new 10-feature model first
            feat_names = model.feature_names_in_ if hasattr(model, "feature_names_in_") else None
            if feat_names is not None and "disease_class_id" in list(feat_names):
                X = pd.DataFrame([[
                    disease_class_id, crop_type_id, pathogen_type_enc,
                    severity, temp, humidity, ph, soil_moisture, 0, urgency_class_enc,
                ]], columns=[
                    "disease_class_id", "crop_type_id", "pathogen_type_enc",
                    "severity", "temperature", "humidity", "ph", "soil_moisture",
                    "geo_risk_enc", "urgency_class_enc",
                ])
            else:
                # Old 6-feature model fallback
                X = pd.DataFrame(
                    [[temp, humidity, ph, soil_moisture, severity, confidence]],
                    columns=["temperature", "humidity", "ph", "soil_moisture", "severity", "confidence"]
                )
            model_pred = model.predict(X)[0]
            # Respect disease-validity constraint
            base_prediction = model_pred if model_pred in valid_actions else valid_actions[0]
        except Exception as e:
            logger.warning(f"recommend model predict error: {e}")
            base_prediction = "monitor"

    weights = load_weights()

    # -------------------------------
    # FEEDBACK LEARNING
    # -------------------------------
    try:
        feedback_score = predict_feedback(
            temp, humidity, ph, soil_moisture, severity
        )
    except Exception:
        feedback_score = 0.5

    # Only score actions that are valid for this disease
    actions = [a for a in weights.keys() if a in valid_actions] or valid_actions

    # -------------------------------
    # SIMULATION ENGINE
    # -------------------------------
    sim_results = simulate_all(actions, severity, feedback_score * 100)

    # ── Get ML model probability scores for each action ──────────────────────
    # The model's probability is now the PRIMARY driver (0.55 weight) so the
    # retrained disease-aware model actually influences the final decision.
    # Adaptive weights and other signals are secondary modifiers.
    model_probs = {}
    try:
        if model is not None:
            feat_names = model.feature_names_in_ if hasattr(model, "feature_names_in_") else None
            if feat_names is not None and "disease_class_id" in list(feat_names):
                import pandas as _pd
                Xp = _pd.DataFrame([[
                    disease_class_id, crop_type_id, pathogen_type_enc,
                    severity, temp, humidity, ph, soil_moisture, 0, urgency_class_enc,
                ]], columns=[
                    "disease_class_id", "crop_type_id", "pathogen_type_enc",
                    "severity", "temperature", "humidity", "ph", "soil_moisture",
                    "geo_risk_enc", "urgency_class_enc",
                ])
                probs = model.predict_proba(Xp)[0]
                model_probs = dict(zip(model.classes_, probs))
    except Exception as _e:
        logger.warning(f"model_proba failed: {_e}")

    base_scores = {}

    for action in actions:
        sim = sim_results[action]

        severity_norm   = severity / 100
        weight_score    = weights.get(action, 0.5)
        future_score    = 1 / (1 + sim["future_score"])
        cost_penalty    = ACTION_COST_INR.get(action, 200) / 300.0
        ml_prob         = model_probs.get(action, 1.0 / max(len(actions), 1))

        if model_probs:
            # New model available — use its probability as primary signal
            score = (
                0.55 * ml_prob +           # ML model probability (primary)
                0.15 * (1 - severity_norm) * (1 if action == "monitor" else 0) +
                0.10 * weight_score +      # adaptive weights (secondary)
                0.10 * feedback_score +    # past effectiveness
                0.10 * future_score        # simulation outcome
                - 0.08 * cost_penalty      # cost efficiency
            )
        else:
            # Fallback: original formula when model unavailable
            score = (
                0.20 * severity_norm +
                0.20 * (confidence / 100) +
                0.20 * weight_score +
                0.20 * feedback_score +
                0.20 * future_score
                - 0.15 * cost_penalty
            )

        base_scores[action] = score

    # -------------------------------
    # BEST ACTION (RL refinement happens later, in pipeline.py Phase 4,
    # using the correct semantic state — urgency × disease × soil — and
    # the disease-validity constraint already applied above). Doing RL
    # fusion here too was redundant and used a mismatched, meaningless
    # state encoding, so it has been removed.
    # -------------------------------
    best_action = max(base_scores, key=base_scores.get)
    final_scores = base_scores

    # -------------------------------
    # ADAPTIVE LEARNING (IMPORTANT) — only touches valid actions
    # -------------------------------
    lr = 0.05
    for action in weights:
        if action not in actions:
            continue
        if action == best_action:
            weights[action] += lr * (1 - weights[action])
        else:
            weights[action] -= lr * weights[action]

    save_weights(weights)

    # -------------------------------
    # DISEASE-SPECIFIC TREATMENT DETAIL (Patent Core)
    # -------------------------------
    if disease_class:
        treatment_detail = get_treatment_detail(disease_class, best_action)
        cultural_practices = get_cultural_practices(disease_class)
    elif crop_type:
        treatment_detail = get_crop_treatment(crop_type, best_action)
        cultural_practices = get_crop_cultural_practices(crop_type)
    else:
        treatment_detail = {}
        cultural_practices = []
    # cultural_practices already set above in unified block

    display_name = TREATMENT_DISPLAY_NAME.get(best_action, best_action)
    product_name = treatment_detail.get("product")
    if product_name:
        display_name = f"{display_name} — {product_name}"

    effectiveness = float(final_scores[best_action]) * 100
    cost = ACTION_COST_INR.get(best_action, 200)
    value_score = effectiveness / (cost + 1)

    return {
        "action": best_action,
        "treatment_name": display_name,
        "type": ACTION_TYPE.get(best_action, "Unknown"),
        "estimated_cost": round(cost, 2),
        "effectiveness": round(effectiveness, 2),
        "value_score": round(value_score, 3),
        "ai_recommended": best_action,

        # ── Disease-specific detail (new) ──────────────────────────────
        "disease_class": disease_class,
        "pathogen_type": pathogen_info.get("pathogen_type"),
        "pathogen": pathogen_info.get("pathogen"),
        "pathogen_notes": pathogen_info.get("notes", ""),
        "valid_actions": valid_actions,
        "treatment_detail": treatment_detail,
        "cultural_practices": cultural_practices,

        "reason": f"Selected from {len(valid_actions)} biologically valid action(s) "
                  f"using ML + RL fusion (score={round(final_scores[best_action], 3)})",
        "urgency": "HIGH" if severity > 50 else "MEDIUM",
        "confidence_score": float(final_scores[best_action]),

        "decision_factors": [
            f"disease_constrained_actions={valid_actions}",
            f"rl_influence=enabled",
            f"future_severity={sim_results[best_action]['future_severity']}",
            f"feedback={feedback_score}",
            f"weight={weights.get(best_action, 0.5)}",
        ]
    }
