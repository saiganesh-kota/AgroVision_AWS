"""
pipeline.py — AgroVision AI Inference Pipeline
────────────────────────────────────────────────────────────────────────────
Phase 0: Image analysis        (leaf model — multi-class aware)
Phase 1: Parallel specialists  (soil, risk, progression, geo, feedback)
Phase 2: Urgency scoring       (urgency_scoring.py — transparent, disclosed)
Phase 3: Disease-aware action  (recommendation_ml.py — biologically constrained)
Phase 4: RL policy             (Q-table, semantic state: urgency × disease × soil)

HONEST DISCLOSURE OF WHAT IS AND ISN'T "LEARNED":
  - The leaf disease CLASSIFICATION is a real trained CNN (multi-class).
  - The ACTION CATEGORY selection (recommendation_ml.py) blends a real
    trained model + RL Q-values + adaptive weights — genuinely adaptive.
  - The URGENCY score is a transparent, disclosed multi-factor weighted
    formula (urgency_scoring.py) — not a black-box classifier. See that
    module's docstring for why this is the honest choice right now, and
    the documented path to making it genuinely learned once real
    post-treatment outcome data accumulates via /feedback.
  - Disease-specific treatment validity (e.g. bacterial diseases cannot
    receive fungicide) comes from disease_treatments.py — a documented
    plant-pathology knowledge base, not an arbitrary rule.

Every external specialist call is wrapped defensively so a single
incompatible/missing sibling module degrades gracefully instead of
crashing the whole prediction.
"""

import os
import json
import logging

# ── Module-level cache for class_names.json ───────────────────────────────────
# Populated on first call to _get_class_names_cache().
# Avoids re-reading and re-parsing the JSON file on every prediction request
# (was previously done on every call to _resolve_disease_class_id and
# _disease_band — both called once per pipeline run).
_CLASS_NAMES_CACHE: dict | None = None   # {int_index: label_str}
_LABEL_TO_IDX_CACHE: dict | None = None  # {label_str: int_index}
_DISEASE_BANDS_CACHE: dict | None = None # {int_index: band_int}

# Pathogen-type → disease band encoding (matches urgency_scoring convention)
# 0 = healthy / abiotic   1 = fungal / other   2 = bacterial   3 = viral
_PATHOGEN_BAND_MAP = {
    "none": 0, "healthy": 0, "abiotic": 0,
    "fungal": 1, "oomycete": 1, "algal": 1, "pest": 1, "unknown": 1,
    "bacterial": 2,
    "viral": 3,
}

logger   = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

from disease_treatments import (
    parse_disease_label, get_pathogen_info, get_weather_class,
    ensure_configs_exist, ACTION_TYPE, ACTION_COST_INR, TREATMENT_DISPLAY_NAME,
    get_crop_fallback, get_crop_valid_actions, get_crop_treatment,
    get_crop_cultural_practices, is_crop_in_model, get_full_treatment_plan,
    get_treatment_detail, CROP_NAME_ALIASES, DISEASE_DB,
)


def _normalize_crop_name(name: str) -> str:
    """Lowercase + apply known aliases so 'Corn' and 'Maize' compare equal,
    'Eggplant' and 'Brinjal' compare equal, etc."""
    if not name:
        return ""
    key = name.strip().lower()
    return CROP_NAME_ALIASES.get(key, key)

# Self-heal missing config files on import — never crash from a missing JSON
ensure_configs_exist(BASE_DIR)

from advanced_predict          import predict_leaf
from action_simulator           import simulate_action, simulate_all
from recommendation_ml          import predict_recommendation
from rl_engine                  import get_state, choose_action, compute_reward, update_q
from urgency_scoring            import predict_urgency

# ── Optional / best-effort specialist imports ──────────────────────────────
def _optional_import(module_name, attr_name):
    try:
        mod = __import__(module_name, fromlist=[attr_name])
        return getattr(mod, attr_name)
    except Exception as e:
        logger.warning(f"Optional module '{module_name}.{attr_name}' unavailable: {e}")
        return None

is_leaf_image           = _optional_import("leaf_validator", "is_leaf_image")
predict_soil             = _optional_import("predict", "predict_soil")
predict_risk             = _optional_import("fusion_predict", "predict_risk")
predict_decision         = _optional_import("decision_ml", "predict_decision")
predict_geo_advanced     = _optional_import("geo_predict", "predict_geo_advanced")
predict_future_severity  = _optional_import("progression_predict", "predict_future_severity")
calculate_health_score   = _optional_import("scoring_engine", "calculate_health_score")
health_breakdown         = _optional_import("scoring_engine", "health_breakdown")
generate_pest_alerts     = _optional_import("pest_alerts", "generate_pest_alerts")
explain_score            = _optional_import("explainability", "explain_score")
explain_factors          = _optional_import("explainability", "explain_factors")
identify_disease         = _optional_import("disease_mapper", "identify_disease")
analyse_weather_risk     = _optional_import("weather_disease_engine", "analyse_weather_risk")
predict_feedback         = _optional_import("feedback_predict", "predict_feedback")
get_geo_momentum         = _optional_import("geo_memory", "compute_momentum")
update_geo_memory        = _optional_import("geo_memory", "update_memory")
predict_treatment        = _optional_import("disease_treatment_predict", "predict_treatment")
enrich_spatial_context   = _optional_import("geo_spatial_engine", "enrich_with_spatial_context")


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def get_disease_stage(severity: float) -> str:
    if severity < 10: return "Early"
    if severity < 30: return "Moderate"
    return "Severe"


ACTION_MAP = {
    "fungicide":     "Apply antifungal spray",
    "bactericide":   "Apply bactericide spray",
    "soil_fix":      "Improve soil using compost",
    "ph_correction": "Adjust soil pH",
    "irrigation":    "Increase irrigation",
    "monitor":       "Monitor crop regularly",
}

_SOIL_ENC = {"poor": 0, "moderate": 1, "good": 2}


def _soil_class_enc(soil_label: str) -> int:
    return _SOIL_ENC.get((soil_label or "moderate").strip().lower(), 1)


def _get_class_names_cache() -> tuple[dict, dict, dict]:
    """
    Load and cache class_names.json on first call.
    Returns (class_names, label_to_idx, disease_bands).

    disease_bands is read from class_names.json if the key is present.
    If absent, it is derived at runtime from DISEASE_DB.pathogen_type —
    this ensures urgency_scoring and the RL state encoder receive the
    correct pathogen band even if class_names.json was saved without it.
    """
    global _CLASS_NAMES_CACHE, _LABEL_TO_IDX_CACHE, _DISEASE_BANDS_CACHE

    if _CLASS_NAMES_CACHE is not None:
        return _CLASS_NAMES_CACHE, _LABEL_TO_IDX_CACHE, _DISEASE_BANDS_CACHE

    path = os.path.join(BASE_DIR, "models", "class_names.json")
    raw  = {}
    if os.path.exists(path):
        try:
            raw = json.load(open(path))
        except Exception as e:
            logger.warning("Failed to load class_names.json: %s", e)

    # Build forward and reverse maps
    _CLASS_NAMES_CACHE  = {int(k): v for k, v in raw.items() if k != "disease_bands"}
    _LABEL_TO_IDX_CACHE = {v: int(k) for k, v in raw.items() if k != "disease_bands"}

    # Build disease_bands — prefer JSON key, fall back to DISEASE_DB derivation
    if "disease_bands" in raw and raw["disease_bands"]:
        _DISEASE_BANDS_CACHE = {int(k): int(v)
                                 for k, v in raw["disease_bands"].items()}
        logger.debug("disease_bands loaded from class_names.json (%d entries)",
                     len(_DISEASE_BANDS_CACHE))
    else:
        # Derive from DISEASE_DB at runtime — avoids wrong band=1 for all diseases
        _DISEASE_BANDS_CACHE = {}
        for label, entry in DISEASE_DB.items():
            idx = _LABEL_TO_IDX_CACHE.get(label)
            if idx is None:
                continue
            ptype = entry.get("pathogen_type", "unknown").lower()
            base  = ptype.split("(")[0].split("/")[0].strip()
            _DISEASE_BANDS_CACHE[idx] = _PATHOGEN_BAND_MAP.get(base, 1)
        # Healthy classes by label name
        for label, idx in _LABEL_TO_IDX_CACHE.items():
            if "healthy" in label.lower() and idx not in _DISEASE_BANDS_CACHE:
                _DISEASE_BANDS_CACHE[idx] = 0
        logger.info(
            "disease_bands derived from DISEASE_DB (%d entries — "
            "add 'disease_bands' key to class_names.json to use static values)",
            len(_DISEASE_BANDS_CACHE)
        )

    return _CLASS_NAMES_CACHE, _LABEL_TO_IDX_CACHE, _DISEASE_BANDS_CACHE


def _resolve_disease_class_id(disease_class: str) -> int:
    """Reverse-lookup the numeric class index for a raw disease label.
    Result is O(1) after first call — uses the cached reverse map."""
    if not disease_class:
        return -1
    _, label_to_idx, _ = _get_class_names_cache()
    return label_to_idx.get(disease_class, -1)


def _disease_band(disease_class_id: int) -> int:
    """0=healthy  1=fungal/other  2=bacterial  3=viral.
    Result is O(1) after first call — uses the cached bands map."""
    if disease_class_id < 0:
        return 1
    _, _, bands = _get_class_names_cache()
    return bands.get(disease_class_id, 1)


def _build_treatment_comparison(sim_results: dict, base_severity: float) -> list:
    rows = []
    for action, sim in sim_results.items():
        sev_after = float(sim.get("future_severity", base_severity))
        reduction = max(0.0, base_severity - sev_after)
        effectiveness = round(min(reduction / max(base_severity, 1.0), 1.0), 4)
        cost_inr = ACTION_COST_INR.get(action, 100)
        cost_norm = cost_inr / 300.0
        value_score = round(effectiveness / (cost_norm + 0.01), 4)
        rows.append({
            "name":           action,
            "treatment_name": TREATMENT_DISPLAY_NAME.get(action, action),
            "cost":           round(cost_norm, 4),
            "cost_inr":       cost_inr,
            "effectiveness":  effectiveness,
            "type":           ACTION_TYPE.get(action, "Unknown"),
            "value_score":    value_score,
            "priority":       "alternative",
        })
    rows.sort(key=lambda r: -r["value_score"])
    if rows:
        rows[0]["priority"] = "primary"
    return rows


def _safe(fn, default, *args, **kwargs):
    """Call an optional specialist function; return default if unavailable or it errors."""
    if fn is None:
        return default
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        logger.warning(f"{getattr(fn, '__name__', fn)} failed: {e}")
        return default


# ═══════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE  — name matches what app.py imports: `full_pipeline`
# ═══════════════════════════════════════════════════════════════════════════

def full_pipeline(image_path, temp, humidity, ph, rainfall, lat=20.5, lon=78.9, crop_type=None):

    # ── LEAF VALIDATION (optional) ─────────────────────────────────────────
    if is_leaf_image:
        is_leaf, reason = _safe(is_leaf_image, (True, ""), image_path)
        if not is_leaf:
            return {"error": reason, "status": "not_a_leaf", "is_leaf": False}

    # ── PHASE 0: LEAF MODEL ─────────────────────────────────────────────────
    leaf_result = predict_leaf(image_path)
    if "error" in leaf_result and leaf_result.get("label") in ("Model Missing", "Error"):
        return {"error": leaf_result.get("error", "Leaf model unavailable"), "status": "model_error"}

    raw_label      = leaf_result["label"]
    model_source   = leaf_result.get("source", "unknown")
    confidence     = float(leaf_result["confidence"])
    severity       = float(leaf_result["severity"])
    severity_level = leaf_result["severity_level"]
    disease_stage  = get_disease_stage(severity)

    disease_class = None
    crop_in_model = False
    crop_mismatch_note = None
    if model_source == "multiclass_model":
        parsed   = parse_disease_label(raw_label)
        cnn_crop = parsed["crop"]
        user_crop = (crop_type.strip() if crop_type and crop_type.strip().lower()
                     not in ("unknown", "", "none") else None)

        cnn_in_model  = True   # the CNN's own prediction is always one of its 84 classes
        user_in_model = is_crop_in_model(user_crop) if user_crop else None
        crops_disagree = bool(user_crop) and _normalize_crop_name(user_crop) != _normalize_crop_name(cnn_crop)

        if user_crop and crops_disagree:
            # The CNN's specific disease guess is for a DIFFERENT crop than
            # what the user says this is — regardless of whether that crop
            # is itself one of the 21 trained ones, pairing the user's crop
            # name with a disease/pathogen description lifted from a
            # completely different crop's class would be scientifically
            # nonsensical (e.g. "Mango" + a Soybean-specific bacterium).
            # Discard the CNN's cross-crop guess and use honest crop-level
            # fallback guidance for the crop the user actually said they have.
            crop          = user_crop
            crop_in_model = bool(user_in_model)
            crop_fb       = get_crop_fallback(crop)
            common        = ", ".join(crop_fb.get("common_diseases", [])[:4])
            pathogen_type = crop_fb.get("dominant_pathogen_type", "unknown")
            disease_name  = "Disease detected" if severity > 5 else "Healthy"
            disease_class = None
            if user_in_model:
                disease_desc = (
                    f"The AI's visual analysis matched this leaf to {cnn_crop} training data instead "
                    f"of {crop} ({confidence:.0f}% confidence), so that disease-specific guess has been "
                    f"discarded as unreliable for {crop}. Showing general {crop} disease guidance instead. "
                    f"Likely pathogens: {common or 'varies'}. Dominant pathogen type: {pathogen_type}."
                )
                crop_mismatch_note = (
                    f"🔴 Crop mismatch: you selected {user_crop}, but the AI's visual analysis matched "
                    f"this leaf to {cnn_crop} training data instead ({confidence:.0f}% confidence). "
                    f"This usually means the photo is unclear, poorly lit, or doesn't clearly show "
                    f"{user_crop}-specific features. Showing general {user_crop} guidance below instead "
                    f"of the (likely wrong) {cnn_crop}-specific diagnosis."
                )
            else:
                disease_desc = (
                    f"'{crop}' is not yet one of the 21 crop types this model was trained on, so its "
                    f"raw image classification ({cnn_crop} — {parsed['disease_name']}, {confidence:.0f}% "
                    f"confidence) does not actually apply here and has been discarded. Showing general "
                    f"{crop} disease guidance instead. Likely pathogens: {common or 'varies'}. "
                    f"Dominant pathogen type: {pathogen_type}."
                )
                crop_mismatch_note = (
                    f"🔴 Crop mismatch: you selected {user_crop}, but this isn't one of the model's 21 "
                    f"trained crops, so its disease-specific guess has been replaced with general "
                    f"{user_crop} guidance below. For a confirmed diagnosis, compare against the photo "
                    f"yourself or consult an agricultural extension officer."
                )
            disease_method      = "crop_fallback_after_cnn_mismatch"
            disease_confidence  = confidence
        else:
            crop          = user_crop or cnn_crop
            disease_name  = parsed["disease_name"]
            disease_class = parsed["raw_label"]
            crop_in_model = True
            pathogen      = get_pathogen_info(disease_class)
            disease_desc  = (f"{pathogen.get('pathogen','Unknown pathogen')} — {pathogen.get('pathogen_type','unknown')} disease"
                              if not parsed["is_healthy"] else "No significant disease symptoms detected.")
            disease_method = "multiclass_cnn_model"
            disease_confidence = confidence
    else:
        # Resolve effective crop name — never pass "Unknown" downstream
        if crop_type and crop_type.strip().lower() not in ("unknown", "", "none"):
            crop = crop_type.strip()
        else:
            crop = None   # genuinely unknown — use general fallback

        crop_in_model = is_crop_in_model(crop) if crop else False
        crop_fb = get_crop_fallback(crop) if crop else {}

        if identify_disease and crop and crop.lower() not in ("unknown",):
            disease_info = _safe(
                identify_disease,
                {"disease": "Diseased", "description": "", "confidence": confidence, "method": "fallback"},
                image_path, crop, severity
            )
        else:
            # Unknown crop — colour analysis guess is unreliable, say so clearly
            disease_info = {
                "disease":     "Disease detected" if severity > 5 else "Healthy",
                "description": "",
                "confidence":  confidence,
                "method":      "cv_fallback",
            }

        disease_name = disease_info["disease"]

        if crop_fb:
            # We know the crop — use its specific common diseases
            common = ", ".join(crop_fb.get("common_diseases", [])[:4])
            pathogen_type = crop_fb.get("dominant_pathogen_type", "unknown")
            disease_desc = (
                f"Detected disease symptoms in {crop}. "
                f"Likely pathogens: {common}. "
                f"Dominant pathogen type: {pathogen_type}. "
                f"Recommendations are based on common {crop} diseases in Indian agriculture."
            )
        elif not crop:
            disease_desc = (
                "Crop type not selected. Disease pattern detected via colour analysis. "
                "Select your crop type on the Scan page for more specific recommendations."
            )
        else:
            disease_desc = disease_info.get("description", "")

        disease_method     = disease_info.get("method", "fallback")
        disease_confidence = disease_info.get("confidence", confidence)

    disease_class_id = _resolve_disease_class_id(disease_class)
    disease_band      = _disease_band(disease_class_id)

    # ── PHASE 1: PARALLEL SPECIALISTS ───────────────────────────────────────
    soil          = _safe(predict_soil, "Moderate", temp, humidity, ph, rainfall)
    soil_class_enc = _soil_class_enc(soil)
    soil_moisture = humidity * 0.5 + rainfall * 0.05

    risk = str(_safe(predict_risk, "Medium", temp, humidity, ph, soil_moisture, severity, confidence)).strip().capitalize()
    if risk not in ("Low", "Medium", "High"):
        risk = "Medium"
    composite_risk_enc = {"Low": 0, "Medium": 1, "High": 2}[risk]

    health_score = _safe(calculate_health_score, round(max(0, 100 - severity), 1), crop, severity, soil, humidity, confidence)

    decision = _safe(predict_decision, "monitor", temp, humidity, ph, soil_moisture, severity, confidence)

    future_list = [float(round(v, 2)) for v in _safe(predict_future_severity, [severity], temp, humidity, ph, soil_moisture, severity)]
    future_severity = future_list[-1] if future_list else severity
    if future_severity > 60:   future = "High disease spread expected"
    elif future_severity > 30: future = "Moderate progression expected"
    else:                       future = "Stable condition"

    geo_data        = _safe(predict_geo_advanced, {}, temp, humidity, rainfall, lat, lon)
    geo              = geo_data.get("geo_risk",        "Low")
    geo_probs        = float(geo_data.get("geo_probability", 0))
    outbreak_score   = float(geo_data.get("outbreak_score",  0))
    spread_velocity  = float(geo_data.get("spread_velocity", 0))
    future_spread    = float(geo_data.get("future_spread",   0))
    spread_trend     = float(geo_data.get("spread_trend",    0))
    geo_risk_enc     = {"Low": 0, "Medium": 1, "High": 2}.get(geo, 0)
    outbreak_class_enc = 2 if outbreak_score > 0.6 else (1 if outbreak_score > 0.3 else 0)

    if geo == "High": risk = "High"
    elif geo == "Medium" and risk == "Low": risk = "Medium"

    geo_momentum = float(_safe(get_geo_momentum, 0.0, lat, lon)) if get_geo_momentum else 0.0
    if update_geo_memory:
        _safe(update_geo_memory, None, lat, lon, spread_velocity)

    # ── Geospatial Intelligence Engine — spatial context enrichment ───────────
    # Builds a SpatialAgriRecord associating this scan's multimodal data
    # with its geographic cell; computes geo-conditioned composite severity
    _spatial_partial = {
        "severity":       severity,
        "outbreak_score": outbreak_score,
        "spread_velocity":spread_velocity,
        "future_spread":  future_spread,
    }
    if enrich_spatial_context:
        _safe(enrich_spatial_context, None, lat, lon, _spatial_partial)
        # Update severity with geo-conditioned value if available
        geo_cond_sev = _spatial_partial.get("geo_conditioned_severity")
        if geo_cond_sev is not None:
            severity = float(geo_cond_sev)   # authoritative composite severity
    cell_id_val        = _spatial_partial.get("cell_id")
    geo_severity_level = _spatial_partial.get("geo_severity_level", severity_level)
    ndvi_proxy         = _spatial_partial.get("ndvi_proxy", 0.0)
    ndvi_depletion     = _spatial_partial.get("ndvi_depletion", 0.0)
    neighbor_risk      = _spatial_partial.get("neighbor_risk", 0.0)
    temporal_momentum  = _spatial_partial.get("temporal_momentum", 0.0)
    adjacent_cells_val = _spatial_partial.get("adjacent_cells", [])
    cell_disease_density = _spatial_partial.get("cell_disease_density", 0.0)

    pest_alerts_list = _safe(generate_pest_alerts, [], crop, temp, humidity, severity, geo)
    weather_risk      = _safe(analyse_weather_risk, {}, temp, humidity, rainfall, crop)

    # Prior treatment effectiveness for THIS disease context (neutral default
    # if no follow-up history is available yet — see feedback_predict.py)
    treatment_effectiveness = _safe(
        predict_feedback, 0.5,
        temp, humidity, ph, soil_moisture, severity,
        soil_class_enc=soil_class_enc,
    )
    if not isinstance(treatment_effectiveness, (int, float)):
        treatment_effectiveness = 0.5

    # ── PHASE 2: URGENCY SCORING (transparent, disclosed) ───────────────────
    urgency_result = predict_urgency(
        severity=severity,
        disease_confidence=confidence,
        disease_class_id=max(0, disease_class_id),
        soil_class_enc=soil_class_enc,
        soil_prob_poor=1.0 if soil_class_enc == 0 else 0.0,
        composite_risk_enc=composite_risk_enc,
        composite_risk_prob_high=1.0 if risk == "High" else 0.0,
        severity_day7=future_severity,
        geo_risk_enc=geo_risk_enc,
        geo_risk_prob_high=1.0 if geo == "High" else 0.0,
        outbreak_class_enc=outbreak_class_enc,
        outbreak_prob_outbreak=outbreak_score,
        spread_velocity=spread_velocity,
        geo_momentum=geo_momentum,
        treatment_effectiveness=float(treatment_effectiveness),
    )
    urgency_class     = urgency_result["urgency_class"]
    urgency_class_enc = urgency_result["urgency_class_enc"]

    # ── PHASE 3: DISEASE-AWARE ACTION SELECTION ─────────────────────────────
    rec_result    = predict_recommendation(temp, humidity, ph, soil_moisture, severity, confidence, disease_class=disease_class, crop_type=crop)
    best_action   = rec_result.get("action", "monitor") if isinstance(rec_result, dict) else str(rec_result)
    rec_details   = rec_result if isinstance(rec_result, dict) else {}
    valid_actions = rec_details.get("valid_actions", list(ACTION_MAP.keys()))

    # ── PHASE 3.5: Optional specific-product enhancement ────────────────────
    if predict_treatment and disease_class_id >= 0:
        treat_enhance = _safe(
            predict_treatment, None,
            disease_class_id=disease_class_id, severity=severity,
            temperature=temp, humidity=humidity, urgency_class_enc=urgency_class_enc,
        )
        if treat_enhance:
            rec_details["model_predicted_treatment"] = treat_enhance.get("treatment")
            rec_details["model_predicted_organic"]    = treat_enhance.get("organic_treatment")

    # ── PHASE 4: RL POLICY (semantic state) ──────────────────────────────────
    state     = get_state(urgency_class_enc, max(0, disease_class_id), soil_class_enc)
    rl_action = choose_action(state)
    action    = rl_action if (rl_action and rl_action in valid_actions) else best_action

    # BUGFIX: when RL overrides recommendation_ml.py's original pick, the
    # treatment_name/treatment_detail/type/cost fields in rec_details were
    # still computed for the OLD pre-RL action — e.g. action could become
    # "fungicide" while treatment_name still read "Monitoring" and
    # treatment_detail stayed an empty dict. Recompute everything for
    # whichever action actually wins, so what's displayed always matches
    # what was decided.
    if action != rec_details.get("action"):
        if disease_class:
            fresh_detail = get_treatment_detail(disease_class, action)
        elif crop:
            fresh_detail = get_crop_treatment(crop, action)
        else:
            fresh_detail = {}
        fresh_display = TREATMENT_DISPLAY_NAME.get(action, action)
        if fresh_detail.get("product"):
            fresh_display = f"{fresh_display} — {fresh_detail['product']}"
        rec_details["treatment_detail"] = fresh_detail
        rec_details["treatment_name"]   = fresh_display
        rec_details["type"]             = ACTION_TYPE.get(action, "Unknown")
        rec_details["estimated_cost"]   = ACTION_COST_INR.get(action, 200)
    rec_details["action"]         = action
    rec_details["ai_recommended"] = action

    new_severity, new_risk = simulate_action(action, severity, risk)
    reward = compute_reward(severity, new_severity, risk, new_risk, effectiveness_score=float(treatment_effectiveness))
    update_q(state, action, reward)

    sim_all = simulate_all(valid_actions, severity, float(treatment_effectiveness) * 100)
    treatment_comparison = _build_treatment_comparison(sim_all, severity)
    best_value_action       = max(treatment_comparison, key=lambda r: r["value_score"],   default={}).get("name")
    best_performance_action = max(treatment_comparison, key=lambda r: r["effectiveness"], default={}).get("name")

    # ── FULL CATEGORIZED TREATMENT PLAN (chemical + organic + cultural) ────
    # This is the rich, multi-option menu — every valid action's product AND
    # organic alternative, plus deduplicated cultural/traditional practices —
    # rather than just the single action the ML+RL engine happened to pick.
    treatment_plan = get_full_treatment_plan(disease_class=disease_class, crop_type=crop)

    # ── EXPLAINABILITY ────────────────────────────────────────────────────
    explainability  = _safe(explain_score, round(min(100, confidence), 1), confidence, severity, risk)
    xai_factor_list = _safe(explain_factors, [], confidence, severity, risk, geo_risk=geo, humidity=humidity, spread_velocity=spread_velocity)
    health_components = _safe(health_breakdown, {}, crop, severity, soil, humidity, confidence)
    action_text     = ACTION_MAP.get(action, "Monitor crop regularly")

    alerts = []
    if crop_mismatch_note:
        alerts.append(crop_mismatch_note)
    is_healthy_pred = model_source == "multiclass_model" and parsed["is_healthy"]
    if model_source == "multiclass_model" and confidence < 60 and not is_healthy_pred and not crop_mismatch_note:
        alerts.append(
            f"⚠️ Low confidence ({confidence:.0f}%) — this leaf may belong to a crop the AI "
            f"model wasn't trained on (currently supports 21 crop types). Treat this diagnosis "
            f"with caution, or select your actual crop manually for a more reliable fallback result."
        )
    if future_severity > 60 or geo == "High":
        alerts.append(f"🔴 Critical alert: {future}. Immediate action required.")
    elif future_severity > 40:
        alerts.append(f"🟠 Warning: {future}. Monitor closely.")
    if spread_velocity > 0.3:
        alerts.append(f"⚠️ Disease spreading in your area (velocity={spread_velocity:.3f}).")
    if rec_details.get("pathogen_type") == "bacterial":
        alerts.append("🦠 Bacterial infection — fungicide will NOT work. Bactericide required.")

    xai_factors = {
        "humidity_impact":      round(min(humidity / 100.0, 1.0), 4),
        "geo_outbreak_risk":    round(geo_probs, 4),
        "severity_weight":      round(min(severity / 100.0, 1.0), 4),
        "future_prediction_7d": round(min(future_severity / 100.0, 1.0), 4),
        "spread_trend_factor":  round(min(abs(spread_trend), 1.0), 4),
        "urgency_composite_score": urgency_result.get("composite_score"),
        "urgency_top_factors":     urgency_result.get("top_factors"),
        "urgency_method":          urgency_result.get("method"),
    }

    return {
        "crop": crop, "crop_type": crop, "crop_in_model": crop_in_model,
        "disease_status": ("Healthy" if (disease_class and "healthy" in disease_class.lower())
                            else (disease_class if disease_class else disease_name)),
        "disease": disease_name, "disease_class": disease_class,
        "disease_description": disease_desc, "disease_confidence": disease_confidence,
        "disease_method": disease_method,
        "pathogen_type": rec_details.get("pathogen_type"), "pathogen": rec_details.get("pathogen"),
        "confidence": confidence, "soil": soil,
        "severity": severity, "severity_level": severity_level, "severity_score": round(severity / 100.0, 4),
        "disease_stage": disease_stage, "health_score": health_score, "risk": risk,
        "decision": str(decision), "is_leaf": True, "model_source": model_source,

        "future": future, "future_severity": future_severity, "future_7days": future_list,

        "geo_risk": geo, "geo_probability": geo_probs, "outbreak_score": outbreak_score,
        "spread_velocity": spread_velocity, "future_spread": future_spread, "spread_trend": spread_trend,

        # ── Geospatial Intelligence Engine outputs ─────────────────────────────
        "geo_conditioned_severity": _spatial_partial.get("geo_conditioned_severity"),
        "geo_severity_level":       geo_severity_level,
        "cell_id":                  cell_id_val,
        "ndvi_proxy":               ndvi_proxy,
        "ndvi_depletion":           ndvi_depletion,
        "neighbor_risk":            neighbor_risk,
        "temporal_momentum":        temporal_momentum,
        "adjacent_cells":           adjacent_cells_val,
        "cell_disease_density":     cell_disease_density,

        "urgency_class": urgency_class, "urgency_class_enc": urgency_class_enc,
        "urgency_confidence": urgency_result.get("confidence"),

        "recommendation": action_text, "recommendation_action": action,
        "recommendation_details": rec_details, "cultural_practices": rec_details.get("cultural_practices", []),
        "treatment_plan": treatment_plan,

        "recommendations": treatment_comparison,
        "best_value": best_value_action, "best_performance": best_performance_action,
        "ai_recommended": action,

        "explainability": explainability, "xai_factors": xai_factors,
        "xai_factor_list": xai_factor_list, "health_components": health_components,

        "alerts": alerts, "pest_alerts": pest_alerts_list, "weather_risk": weather_risk,
    }
