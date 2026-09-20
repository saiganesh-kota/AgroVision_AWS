"""
geo_forecast_engine.py — Disease Geospatial Forecasting Engine (Patent Feature XIII)
──────────────────────────────────────────────────────────────────────────────────────
Simulates future disease spread across a geographic grid and provides:

  • 7-day forward zone forecasts with daily risk scores
  • Heat-map data (compound risk per 0.1° grid cell)
  • Top-N outbreak hotspot detection
  • Structured zone-level disease alerts

Spread model:
  SIR-inspired cellular automaton on the 0.1° grid.
  Each infected cell spreads to adjacent cells based on:
    - Current cell risk score
    - Seasonal wind direction bias (India NE/SW monsoon calendar)
    - Climate amplification factor (humidity + rainfall)
    - Temporal acceleration (momentum)
    - Natural disease decay between application days
"""
import math
import logging
from datetime import datetime, timezone, timedelta

import numpy as np

from geo_spatial_engine import (
    get_all_cell_summaries, get_spatial_record,
    cell_id, cell_center, adjacent_cells, haversine_km,
    _get_grid_index, _cell_stats, _temporal_momentum,
)

logger = logging.getLogger(__name__)

# ── India prevailing wind vectors by calendar month ──────────────────────────
# (dlat, dlon) direction bias — positive lat = northward, positive lon = eastward
# Jun–Sep: SW monsoon (wind FROM SW → spread moves NE)
# Oct–Feb: NE monsoon (wind FROM NE → spread moves SW)
_MONTH_WIND = {
    1:  ( 0.3, -0.2),   # Jan:  NE monsoon
    2:  ( 0.3, -0.2),   # Feb:  NE
    3:  ( 0.1,  0.1),   # Mar:  transitional
    4:  (-0.1,  0.3),   # Apr:  pre-monsoon westerlies
    5:  (-0.2,  0.3),   # May:  pre-monsoon SW
    6:  (-0.4,  0.4),   # Jun:  SW monsoon onset
    7:  (-0.4,  0.4),   # Jul:  SW monsoon peak
    8:  (-0.3,  0.4),   # Aug:  SW
    9:  (-0.2,  0.2),   # Sep:  SW weakening
    10: ( 0.1, -0.1),   # Oct:  NE onset
    11: ( 0.3, -0.2),   # Nov:  NE monsoon
    12: ( 0.3, -0.2),   # Dec:  NE
}

# Base probability of disease spreading to each adjacent cell per simulation day
BASE_SPREAD_PROB = 0.10


def _wind_factor(dlat: int, dlon: int, month: int) -> float:
    """
    Direction-weighted spread multiplier.
    Returns ≈1.8 for downwind direction, ≈0.4 for upwind.
    """
    wlat, wlon = _MONTH_WIND.get(month, (0.0, 0.0))
    mag = math.sqrt(dlat ** 2 + dlon ** 2) or 1.0
    dot = (dlat * wlat + dlon * wlon) / mag
    return float(np.clip(1.0 + 0.80 * dot, 0.40, 1.80))


def _climate_factor(humidity: float = 65.0, rainfall: float = 80.0) -> float:
    """Higher humidity + rainfall → faster disease spread."""
    hf = float(np.clip((humidity - 40.0) / 60.0, 0.0, 1.0))
    rf = float(np.clip(rainfall / 200.0, 0.0, 1.0))
    return 0.50 + 0.50 * (hf * 0.60 + rf * 0.40)


def _dominant_direction(month: int) -> str:
    """Cardinal/intercardinal name of the dominant spread direction this month."""
    wlat, wlon = _MONTH_WIND.get(month, (0.0, 0.0))
    dirs = {
        (1, 0): "N",  (-1, 0): "S",  (0, 1): "E",  (0, -1): "W",
        (1, 1): "NE", (1, -1): "NW", (-1, 1): "SE", (-1, -1): "SW",
    }
    best, best_dot = "N", -99.0
    for (dlat, dlon), name in dirs.items():
        mag = math.sqrt(dlat ** 2 + dlon ** 2)
        dot = (dlat * wlat + dlon * wlon) / mag
        if dot > best_dot:
            best_dot = dot
            best = name
    return best


# ══════════════════════════════════════════════════════════════════════════════
# CELLULAR AUTOMATON SPREAD SIMULATION
# ══════════════════════════════════════════════════════════════════════════════

def simulate_spread_grid(
    center_lat:  float,
    center_lon:  float,
    days:        int   = 7,
    grid_radius: int   = 4,
    humidity:    float = 65.0,
    rainfall:    float = 80.0,
) -> dict:
    """
    SIR-inspired cellular automaton disease spread simulation.

    Initialises a (2×grid_radius+1)² grid of cells from real scan data,
    then propagates infection day-by-day using wind-direction-biased
    spread probabilities and natural decay.

    Returns:
        {cell_id: [risk_day0, risk_day1, ..., risk_dayN]}
    """
    month = datetime.now().month
    clim  = _climate_factor(humidity, rainfall)
    index = _get_grid_index()

    base_lat = math.floor(center_lat / 0.1) * 0.1
    base_lon = math.floor(center_lon / 0.1) * 0.1

    # ── Initialise grid from real data ────────────────────────────────────
    grid = {}
    for dlat in range(-grid_radius, grid_radius + 1):
        for dlon in range(-grid_radius, grid_radius + 1):
            clat = round(base_lat + dlat * 0.1, 1)
            clon = round(base_lon + dlon * 0.1, 1)
            cid  = f"{clat:.1f}_{clon:.1f}"
            cs   = index.get(cid, [])
            if cs:
                st   = _cell_stats(cs)
                risk = st["avg_severity"] / 100.0
                # Boost initial risk for cells with recent activity
                mom  = _temporal_momentum(cs)
                risk = float(np.clip(risk * (1.0 + mom * 0.3), 0.0, 1.0))
            else:
                risk = 0.0
            grid[cid] = risk

    history = {cid: [v] for cid, v in grid.items()}

    # ── Day-by-day propagation ─────────────────────────────────────────────
    for _day in range(1, days + 1):
        new_grid = dict(grid)

        for cid, risk in grid.items():
            if risk < 0.04:
                continue  # below infection threshold

            lat_str, lon_str = cid.split("_", 1) if "_" in cid else (cid, "0")
            try:
                clat = float(lat_str)
                clon = float(lon_str)
            except ValueError:
                continue

            for dlat in (-1, 0, 1):
                for dlon in (-1, 0, 1):
                    if dlat == 0 and dlon == 0:
                        continue
                    nlat = round(clat + dlat * 0.1, 1)
                    nlon = round(clon + dlon * 0.1, 1)
                    ncid = f"{nlat:.1f}_{nlon:.1f}"
                    if ncid not in new_grid:
                        continue

                    wf    = _wind_factor(dlat, dlon, month)
                    prob  = BASE_SPREAD_PROB * risk * clim * wf
                    delta = prob * (risk * 0.5)
                    new_grid[ncid] = float(np.clip(new_grid[ncid] + delta, 0.0, 1.0))

            # Natural decay in current cell (disease resolves / treatment effect)
            new_grid[cid] = float(np.clip(grid[cid] * 0.93, 0.0, 1.0))

        grid = new_grid
        for cid in history:
            history[cid].append(grid.get(cid, 0.0))

    return history


# ══════════════════════════════════════════════════════════════════════════════
# 7-DAY ZONE FORECAST
# ══════════════════════════════════════════════════════════════════════════════

def forecast_zone(
    lat:      float,
    lon:      float,
    days:     int   = 7,
    humidity: float = 65.0,
    rainfall: float = 80.0,
) -> dict:
    """
    Generate a 7-day geospatial disease spread forecast for a specific location.

    Returns:
        {
          lat, lon, cell_id,
          current_risk, trend ("increasing"|"stable"|"decreasing"),
          peak_risk_day, peak_risk_score,
          spread_direction, dominant_disease,
          forecast: [
            { date, day, risk_score, risk_pct, risk_level,
              spread_direction, dominant_disease, confidence }
          ]
        }
    """
    index = _get_grid_index()
    cid   = cell_id(lat, lon)
    month = datetime.now().month
    today = datetime.now(timezone.utc).date()

    history        = simulate_spread_grid(lat, lon, days=days,
                                           humidity=humidity, rainfall=rainfall)
    center_series  = history.get(cid, [0.0] * (days + 1))

    # Dominant disease in this cell
    cell_scans = index.get(cid, [])
    dom_disease = None
    if cell_scans:
        st = _cell_stats(cell_scans)
        dom_disease = st.get("dominant_disease")

    spread_dir = _dominant_direction(month)

    forecast_days = []
    for d in range(1, days + 1):
        risk       = center_series[d] if d < len(center_series) else center_series[-1]
        risk_level = (
            "Critical" if risk >= 0.60 else
            "High"     if risk >= 0.35 else
            "Moderate" if risk >= 0.15 else "Low"
        )
        confidence = round(max(0.40, 0.95 - d * 0.07), 2)
        forecast_days.append({
            "date":             (today + timedelta(days=d)).isoformat(),
            "day":              d,
            "risk_score":       round(risk, 4),
            "risk_pct":         round(risk * 100, 1),
            "risk_level":       risk_level,
            "spread_direction": spread_dir,
            "dominant_disease": dom_disease,
            "confidence":       confidence,
        })

    # Trend analysis
    if len(center_series) >= 3:
        early = float(np.mean(center_series[1:3]))
        late  = float(np.mean(center_series[-2:]))
        trend = "increasing" if late > early + 0.03 else \
                "decreasing" if late < early - 0.03 else "stable"
    else:
        trend = "stable"

    peak_idx   = int(np.argmax([f["risk_score"] for f in forecast_days])) if forecast_days else 0
    peak_score = forecast_days[peak_idx]["risk_score"] if forecast_days else 0.0

    return {
        "lat":              round(lat, 6),
        "lon":              round(lon, 6),
        "cell_id":          cid,
        "current_risk":     round(center_series[0], 4),
        "current_risk_pct": round(center_series[0] * 100, 1),
        "trend":            trend,
        "peak_risk_day":    peak_idx + 1,
        "peak_risk_score":  round(peak_score, 4),
        "spread_direction": spread_dir,
        "dominant_disease": dom_disease,
        "forecast":         forecast_days,
    }


# ══════════════════════════════════════════════════════════════════════════════
# HEAT-MAP DATA GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def generate_heatmap(
    center_lat: float,
    center_lon: float,
    radius_km:  float = 300.0,
    days:       int   = 30,
) -> list:
    """
    Generate heat-map data points for all grid cells within `radius_km`
    of the center coordinate.

    Each point encodes risk_score, risk_level, dominant disease/crop,
    and temporal acceleration — ready for Leaflet circle layer rendering.
    """
    summaries = get_all_cell_summaries()
    result    = []
    for s in summaries:
        dist = haversine_km(center_lat, center_lon, s["lat"], s["lon"])
        if dist > radius_km:
            continue
        compound = s["compound_risk"]
        result.append({
            "cell_id":          s["cell_id"],
            "lat":              s["lat"],
            "lon":              s["lon"],
            "risk_score":       compound,
            "risk_pct":         round(compound * 100, 1),
            "risk_level": (
                "Critical" if compound >= 0.60 else
                "High"     if compound >= 0.35 else
                "Moderate" if compound >= 0.15 else "Low"
            ),
            "scan_count":       s["scan_count"],
            "avg_severity":     s["avg_severity"],
            "dominant_disease": s["dominant_disease"],
            "dominant_crop":    s["dominant_crop"],
            "temporal_momentum":s["temporal_momentum"],
            "ndvi_depletion":   s["ndvi_depletion"],
            "distance_km":      round(dist, 1),
        })
    result.sort(key=lambda x: -x["risk_score"])
    return result


# ══════════════════════════════════════════════════════════════════════════════
# OUTBREAK HOTSPOT DETECTION
# ══════════════════════════════════════════════════════════════════════════════

def compute_outbreak_hotspots(top_n: int = 10) -> list:
    """
    Return the top-N grid cells ranked by compound disease risk score.
    Each entry includes full spatial context and a rank label.
    """
    summaries = get_all_cell_summaries()
    hotspots  = []
    for rank, s in enumerate(summaries[:top_n], start=1):
        compound = s["compound_risk"]
        hotspots.append({
            "rank":             rank,
            "cell_id":          s["cell_id"],
            "lat":              s["lat"],
            "lon":              s["lon"],
            "compound_risk":    compound,
            "risk_level": (
                "Critical" if compound >= 0.60 else
                "High"     if compound >= 0.35 else
                "Moderate" if compound >= 0.15 else "Low"
            ),
            "avg_severity":     s["avg_severity"],
            "scan_count":       s["scan_count"],
            "dominant_disease": s["dominant_disease"],
            "dominant_crop":    s["dominant_crop"],
            "temporal_momentum":s["temporal_momentum"],
            "ndvi_depletion":   s["ndvi_depletion"],
        })
    return hotspots


# ══════════════════════════════════════════════════════════════════════════════
# ZONE ALERT GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def generate_zone_alerts(
    lat:       float,
    lon:       float,
    radius_km: float = 200.0,
) -> list:
    """
    Generate structured zone-level disease alerts for cells near a location.

    Returns alerts ordered by severity, each carrying a human-readable
    message suitable for display in the frontend Zone Alerts panel.
    """
    hm     = generate_heatmap(lat, lon, radius_km=radius_km)
    alerts = []

    for cell in hm:
        compound = cell.get("compound_risk") or cell.get("risk_score") or 0.0
        if compound < 0.10:
            continue  # below alertable threshold

        risk_level   = cell["risk_level"]
        sev_rank_map = {"Critical": 4, "High": 3, "Moderate": 2, "Low": 1}
        sev_rank     = sev_rank_map.get(risk_level, 1)

        mom_str = ""
        if cell["temporal_momentum"] > 0.5:
            mom_str = " — RAPIDLY ACCELERATING"
        elif cell["temporal_momentum"] > 0.25:
            mom_str = " — accelerating"

        ndvi_str = ""
        if cell["ndvi_depletion"] > 0.6:
            ndvi_str = " · NDVI severely depleted"
        elif cell["ndvi_depletion"] > 0.35:
            ndvi_str = " · NDVI moderately depleted"

        alerts.append({
            "cell_id":       cell["cell_id"],
            "lat":           cell["lat"],
            "lon":           cell["lon"],
            "risk_level":    risk_level,
            "severity_rank": sev_rank,
            "compound_risk": compound,
            "risk_pct":      round(compound * 100, 1),
            "avg_severity":  cell["avg_severity"],
            "scan_count":    cell["scan_count"],
            "distance_km":   cell["distance_km"],
            "disease":       cell["dominant_disease"] or "Unknown",
            "crop":          cell["dominant_crop"]    or "Unknown",
            "temporal_momentum": cell["temporal_momentum"],
            "ndvi_depletion":    cell["ndvi_depletion"],
            "message": (
                f"{risk_level} risk zone{mom_str}: "
                f"{cell['dominant_disease'] or 'Disease'} in "
                f"{cell['dominant_crop'] or 'crops'} — "
                f"{cell['avg_severity']:.0f}% avg severity, "
                f"{cell['scan_count']} scan{'s' if cell['scan_count'] != 1 else ''}, "
                f"{cell['distance_km']} km away{ndvi_str}"
            ),
        })

    alerts.sort(key=lambda x: (-x["severity_rank"], -x["compound_risk"]))
    return alerts
