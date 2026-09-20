"""
geo_predict.py — Geo Intelligence Engine (Patent Feature IV)
─────────────────────────────────────────────────────────────
Combines a trained geo-ML model with the spread engine and geo-memory
to produce a holistic geo-risk score for any lat/lon.
"""
import os
import logging
import pickle
import pandas as pd
import numpy as np

from spread_engine import compute_spread
from geo_memory   import update_memory, compute_momentum

logger    = logging.getLogger(__name__)
BASE      = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE, "models", "geo_model.pkl")

_model = None


def _load_model():
    global _model
    if _model is None:
        if os.path.exists(MODEL_PATH):
            _model = pickle.load(open(MODEL_PATH, "rb"))
        else:
            logger.warning("geo_model.pkl not found — using heuristic fallback")
    return _model


def predict_geo_advanced(temp: float, humidity: float, rainfall: float,
                         lat: float, lon: float) -> dict:
    """
    Returns:
        geo_risk         : "Low" | "Medium" | "High"
        geo_probability  : float 0-1
        outbreak_score   : float 0-1
        spread_velocity  : float 0-1
        future_spread    : float 0-1
        spread_trend     : float 0-1
    """
    model = _load_model()

    # ── Base probability from geo ML model ────────────────────────────────
    if model is not None:
        try:
            X = pd.DataFrame(
                [[lat, lon, humidity, 1]],
                columns=["lat", "lon", "humidity", "density"]
            )
            base_prob = float(model.predict_proba(X)[0].max())
        except Exception as e:
            logger.warning(f"geo model predict error: {e}")
            base_prob = _heuristic_base_prob(humidity, rainfall)
    else:
        base_prob = _heuristic_base_prob(humidity, rainfall)

    # ── Spread engine ─────────────────────────────────────────────────────
    spread_velocity, outbreak_score, future_spread, spread_trend_raw = compute_spread(lat, lon)

    # ── Geo memory momentum ───────────────────────────────────────────────
    update_memory(lat, lon, spread_velocity)
    spread_trend = float(np.clip(compute_momentum(lat, lon), -1.0, 1.0))

    # ── Final composite score ─────────────────────────────────────────────
    final_score = (
        base_prob      * 0.55 +
        outbreak_score * 0.20 +
        future_spread  * 0.15 +
        max(0.0, spread_trend) * 0.10   # only positive trend raises risk
    )

    if   final_score > 0.70: geo_risk = "High"
    elif final_score > 0.38: geo_risk = "Medium"
    else:                     geo_risk = "Low"

    return {
        "geo_risk":        geo_risk,
        "geo_probability": round(base_prob,       4),
        "outbreak_score":  round(outbreak_score,  4),
        "spread_velocity": round(spread_velocity, 4),
        "future_spread":   round(future_spread,   4),
        "spread_trend":    round(spread_trend,    4),
    }


def _heuristic_base_prob(humidity: float, rainfall: float) -> float:
    """Simple rule when model is unavailable."""
    prob = 0.3
    if humidity > 75:  prob += 0.25
    if humidity > 85:  prob += 0.10
    if rainfall > 120: prob += 0.10
    if rainfall > 200: prob += 0.10
    return float(np.clip(prob, 0.0, 1.0))
