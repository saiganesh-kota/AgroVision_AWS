"""
spread_engine.py — Disease Spread Intelligence (Patent Feature V)
─────────────────────────────────────────────────────────────────
Computes geo-temporal disease spread metrics from historical scan data.
Returns (spread_velocity, outbreak_score, future_spread, spread_trend).
"""
import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

BASE          = os.path.dirname(os.path.abspath(__file__))
FEEDBACK_PATH = os.path.join(BASE, "feedback_data.csv")
SCANS_PATH    = os.path.join(BASE, "scans_db.json")


def _get_days(ts):
    try:
        return max(0, (datetime.now() - datetime.fromisoformat(str(ts))).days)
    except Exception:
        return 0


def compute_spread(lat: float, lon: float) -> tuple:
    """
    Returns (spread_velocity, outbreak_score, future_spread, spread_trend)
    all in range [0.0, 1.0].  Never raises — returns zeros on any error.
    """
    # ── Try to use richer scan DB first ──────────────────────────────────
    scan_df = _load_scans_df()
    if scan_df is not None and len(scan_df) >= 2:
        return _compute_from_scans(scan_df, lat, lon)

    # ── Fall back to feedback CSV ─────────────────────────────────────────
    if not os.path.exists(FEEDBACK_PATH):
        return 0.0, 0.0, 0.0, 0.0

    try:
        df = pd.read_csv(FEEDBACK_PATH)
    except Exception as e:
        logger.warning(f"spread_engine CSV read error: {e}")
        return 0.0, 0.0, 0.0, 0.0

    if "lat" not in df.columns or "lon" not in df.columns or len(df) < 2:
        return 0.0, 0.0, 0.0, 0.0

    return _compute_from_df(df, lat, lon)


def _load_scans_df():
    """Load scans_db.json into a flat DataFrame with lat/lon/severity/timestamp."""
    try:
        import json
        if not os.path.exists(SCANS_PATH):
            return None
        with open(SCANS_PATH) as f:
            scans = json.load(f)
        rows = []
        for s in scans:
            if s.get("lat") and s.get("lon"):
                r = s.get("result") or {}
                rows.append({
                    "lat":       float(s["lat"]),
                    "lon":       float(s["lon"]),
                    "severity":  float(r.get("severity", 0)),
                    "timestamp": s.get("timestamp", ""),
                })
        return pd.DataFrame(rows) if rows else None
    except Exception:
        return None


def _compute_from_df(df, lat, lon, fallback_factor=None):
    df["distance"] = np.sqrt((df["lat"] - lat) ** 2 + (df["lon"] - lon) ** 2)
    nearby = df[df["distance"] < 1.5].copy()

    if len(nearby) < 2:
        nearby = df.copy()
        ff = 0.5
    else:
        ff = fallback_factor or 1.0

    if "timestamp" in nearby.columns:
        nearby["days"] = nearby["timestamp"].apply(_get_days)
    else:
        nearby["days"] = 0

    nearby["weight"] = np.exp(-nearby["days"] / 7.0)

    spread_velocity = float(np.clip(nearby["weight"].mean() * ff, 0.0, 1.0))
    outbreak_score  = float(np.clip(spread_velocity * 0.8, 0.0, 1.0))

    recent = nearby[nearby["days"] < 3]
    older  = nearby[(nearby["days"] >= 3) & (nearby["days"] < 10)]
    spread_trend = float(np.clip(len(recent) / (len(older) + 1), 0.0, 1.0))
    future_spread = float(np.clip(spread_velocity * (1.0 + spread_trend), 0.0, 1.0))

    return (
        round(spread_velocity, 4),
        round(outbreak_score,  4),
        round(future_spread,   4),
        round(spread_trend,    4),
    )


def _compute_from_scans(df, lat, lon):
    """
    Richer calculation using actual scan severity values.
    High-severity nearby scans drive a higher outbreak score.
    """
    df["distance"] = np.sqrt((df["lat"] - lat) ** 2 + (df["lon"] - lon) ** 2)
    nearby = df[df["distance"] < 1.5].copy()
    ff = 1.0
    if len(nearby) < 2:
        nearby = df.copy()
        ff = 0.5

    if "timestamp" in nearby.columns:
        nearby["days"] = nearby["timestamp"].apply(_get_days)
    else:
        nearby["days"] = 0

    nearby["weight"] = np.exp(-nearby["days"] / 7.0)
    nearby["sev_norm"] = nearby.get("severity", pd.Series(0, index=nearby.index)) / 100.0

    # Weighted average severity — heavier weight for recent + severe
    weighted_sev = float(np.average(
        nearby["sev_norm"].fillna(0),
        weights=nearby["weight"]
    ))

    spread_velocity = float(np.clip(weighted_sev * ff, 0.0, 1.0))
    outbreak_score  = float(np.clip(
        spread_velocity * 0.7 + (nearby["sev_norm"] > 0.5).mean() * 0.3,
        0.0, 1.0
    ))

    recent = nearby[nearby["days"] < 3]
    older  = nearby[(nearby["days"] >= 3) & (nearby["days"] < 10)]
    spread_trend  = float(np.clip(len(recent) / (len(older) + 1), 0.0, 1.0))
    future_spread = float(np.clip(spread_velocity * (1.0 + spread_trend), 0.0, 1.0))

    return (
        round(spread_velocity, 4),
        round(outbreak_score,  4),
        round(future_spread,   4),
        round(spread_trend,    4),
    )
