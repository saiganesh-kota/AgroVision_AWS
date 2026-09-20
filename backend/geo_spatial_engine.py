"""
geo_spatial_engine.py — Geospatial Intelligence Engine (Patent Feature XII)
────────────────────────────────────────────────────────────────────────────
Associates multimodal agricultural data with geographic coordinates to
generate richly-enriched spatial agricultural data records (SpatialAgriRecord).

Key concepts:
  GeoGrid   — divides map into 0.1° × 0.1° cells (~11 km²)
  SpatialAgriRecord — unified record: GPS + image + weather + soil + crop + time
  geo_conditioned_severity — composite severity blending image, geo, neighbor,
                              temporal momentum and NDVI depletion proxy
"""
import os
import json
import math
import logging
import threading
from datetime import datetime, timezone, timedelta
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)
BASE       = os.path.dirname(os.path.abspath(__file__))
SCANS_FILE = os.path.join(BASE, "scans_db.json")

# Grid resolution: 0.1° ≈ 11 km
CELL_RES = 0.1
CACHE_TTL = 120   # seconds before grid index is rebuilt

# ── Thread-safe grid-index cache ──────────────────────────────────────────────
_CACHE_LOCK  = threading.Lock()
_GRID_INDEX  = None          # {cell_id: [scan, ...]}
_CACHE_UNTIL = 0.0           # epoch seconds


# ══════════════════════════════════════════════════════════════════════════════
# GRID UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def cell_id(lat: float, lon: float) -> str:
    """Return the 0.1°-resolution grid cell identifier for a coordinate."""
    clat = round(math.floor(lat / CELL_RES) * CELL_RES, 1)
    clon = round(math.floor(lon / CELL_RES) * CELL_RES, 1)
    return f"{clat:.1f}_{clon:.1f}"


def cell_center(cid: str) -> tuple:
    """Return (lat, lon) of the center of a cell."""
    parts = cid.rsplit("_", 1)
    if len(parts) != 2:
        # handle negative lon like "-78.1_20.5"
        parts = cid.split("_")
        if len(parts) >= 2:
            lat = float(parts[0])
            lon = float(parts[1])
        else:
            return 0.0, 0.0
    else:
        lat = float(parts[0])
        lon = float(parts[1])
    return lat + CELL_RES / 2, lon + CELL_RES / 2


def adjacent_cells(lat: float, lon: float, radius: int = 1) -> list:
    """Return cell IDs within `radius` grid steps of the cell containing lat/lon."""
    base_lat = math.floor(lat / CELL_RES) * CELL_RES
    base_lon = math.floor(lon / CELL_RES) * CELL_RES
    cells = []
    for dlat in range(-radius, radius + 1):
        for dlon in range(-radius, radius + 1):
            if dlat == 0 and dlon == 0:
                continue
            nlat = round(base_lat + dlat * CELL_RES, 1)
            nlon = round(base_lon + dlon * CELL_RES, 1)
            cells.append(f"{nlat:.1f}_{nlon:.1f}")
    return cells


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in kilometres."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ══════════════════════════════════════════════════════════════════════════════
# SCAN DATA LOADING + GRID INDEX
# ══════════════════════════════════════════════════════════════════════════════

def _load_scans() -> list:
    """Load scans_db.json. Returns [] on any error."""
    if not os.path.exists(SCANS_FILE):
        return []
    try:
        with open(SCANS_FILE) as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"geo_spatial_engine: scan load failed: {e}")
        return []


def _get_grid_index() -> dict:
    """
    Return cached grid index {cell_id: [scan, ...]}.
    Rebuilds every CACHE_TTL seconds to reflect new scans.
    """
    global _GRID_INDEX, _CACHE_UNTIL
    import time
    now = time.time()
    with _CACHE_LOCK:
        if _GRID_INDEX is not None and now < _CACHE_UNTIL:
            return _GRID_INDEX

        scans = _load_scans()
        index = {}
        for s in scans:
            try:
                lat = float(s["lat"])
                lon = float(s["lon"])
            except (KeyError, TypeError, ValueError):
                continue
            cid = cell_id(lat, lon)
            index.setdefault(cid, []).append(s)

        _GRID_INDEX  = index
        _CACHE_UNTIL = now + CACHE_TTL
        return _GRID_INDEX


def _age_days(ts: str) -> float:
    """Days since a timestamp string. Returns 9999 on parse error."""
    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 86400)
    except Exception:
        return 9999.0


# ══════════════════════════════════════════════════════════════════════════════
# CELL-LEVEL STATS
# ══════════════════════════════════════════════════════════════════════════════

def _cell_stats(scans_in_cell: list) -> dict:
    """Aggregate disease stats for one geographic grid cell."""
    if not scans_in_cell:
        return {
            "count": 0, "avg_severity": 0.0, "max_severity": 0.0,
            "disease_density": 0.0, "recent_count": 0,
            "dominant_disease": None, "dominant_crop": None,
        }

    severities, diseases, crops = [], {}, {}
    recent = 0
    for s in scans_in_cell:
        r   = s.get("result") or {}
        sev = float(s.get("severity") or r.get("severity", 0))
        severities.append(sev)
        dis = s.get("disease") or r.get("disease", "")
        crp = s.get("crop")    or r.get("crop",    "")
        if dis:
            diseases[dis] = diseases.get(dis, 0) + 1
        if crp:
            crops[crp]    = crops.get(crp, 0) + 1
        if _age_days(s.get("timestamp", "")) < 7:
            recent += 1

    count   = len(severities)
    avg_sev = float(np.mean(severities))
    max_sev = float(np.max(severities))
    density = min(1.0, count / 10.0)   # 10+ scans → density 1.0
    dom_dis = max(diseases, key=diseases.get) if diseases else None
    dom_crp = max(crops,    key=crops.get)    if crops    else None

    return {
        "count":            count,
        "avg_severity":     round(avg_sev, 2),
        "max_severity":     round(max_sev, 2),
        "disease_density":  round(density, 4),
        "recent_count":     recent,
        "dominant_disease": dom_dis,
        "dominant_crop":    dom_crp,
    }


def _neighbor_risk(lat: float, lon: float, index: dict) -> float:
    """Weighted average outbreak risk from the 8 adjacent grid cells."""
    ring1 = adjacent_cells(lat, lon, radius=1)
    risk_scores, weights = [], []
    for ncid in ring1:
        ns = index.get(ncid, [])
        if not ns:
            continue
        stats = _cell_stats(ns)
        risk_scores.append(stats["avg_severity"] / 100.0)
        weights.append(1.0)
    if not risk_scores:
        return 0.0
    return float(np.average(risk_scores, weights=weights))


def _temporal_momentum(scans_in_cell: list) -> float:
    """
    How fast is disease accelerating in this cell?
    Ratio of recent (<3 days) to slightly older (3–10 days) scans.
    """
    if len(scans_in_cell) < 2:
        return 0.0
    recent = sum(1 for s in scans_in_cell if _age_days(s.get("timestamp", "")) < 3)
    older  = sum(1 for s in scans_in_cell
                 if 3 <= _age_days(s.get("timestamp", "")) < 10)
    return float(np.clip(recent / (older + 1), 0.0, 1.0))


def _ndvi_proxy(scans_in_cell: list) -> float:
    """
    NDVI depletion proxy: higher avg disease severity → lower NDVI.
    Returns 0.0 (healthy vegetation) to 1.0 (severely depleted).
    """
    if not scans_in_cell:
        return 0.0
    sevs = [
        float(s.get("severity") or (s.get("result") or {}).get("severity", 0))
        for s in scans_in_cell
    ]
    return float(np.clip(np.mean(sevs) / 100.0, 0.0, 1.0))


# ══════════════════════════════════════════════════════════════════════════════
# COMPOSITE DISEASE SEVERITY VALUE
# ══════════════════════════════════════════════════════════════════════════════

def compute_geo_conditioned_severity(
    image_severity:    float,
    outbreak_score:    float,
    neighbor_risk:     float,
    temporal_momentum: float,
    ndvi_depletion:    float,
) -> float:
    """
    Composite disease severity value (0–100) derived from multimodal inputs:

      45%  — raw image-based severity (CNN leaf model output)
      20%  — neighbor cell outbreak risk (geographic context)
      15%  — spread engine outbreak score (historical spread dynamics)
      10%  — temporal momentum (rate of acceleration)
      10%  — NDVI depletion proxy (vegetation health indicator)

    This is the authoritative severity used for treatment decisions when
    geo context is available, replacing the raw image-only value.
    """
    geo_cond = (
        image_severity          * 0.45 +
        neighbor_risk * 100.0   * 0.20 +
        outbreak_score * 100.0  * 0.15 +
        temporal_momentum * 100 * 0.10 +
        ndvi_depletion * 100    * 0.10
    )
    return round(float(np.clip(geo_cond, 0.0, 100.0)), 2)


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC API — SPATIAL RECORD BUILDER
# ══════════════════════════════════════════════════════════════════════════════

def get_spatial_record(lat: float, lon: float,
                        scan_result: Optional[dict] = None) -> dict:
    """
    Build a complete SpatialAgriRecord for any lat/lon.

    Parameters:
        lat, lon    — geographic coordinates
        scan_result — optional live pipeline result dict; when provided,
                      its severity/outbreak values override stored cell stats

    Returns a richly-enriched dict representing the spatial agricultural
    data record for this location. Suitable for the /geo/spatial-record API.
    """
    index      = _get_grid_index()
    cid        = cell_id(lat, lon)
    cell_scans = index.get(cid, [])

    cell_st    = _cell_stats(cell_scans)
    nbr_risk   = _neighbor_risk(lat, lon, index)
    momentum   = _temporal_momentum(cell_scans)
    ndvi_dep   = _ndvi_proxy(cell_scans)

    # Use live result if provided, else stored cell averages
    sr         = scan_result or {}
    image_sev  = float(sr.get("severity",       cell_st["avg_severity"]))
    ob_score   = float(sr.get("outbreak_score",  0.0))
    spd_vel    = float(sr.get("spread_velocity", 0.0))
    future_spd = float(sr.get("future_spread",   0.0))

    geo_cond_sev = compute_geo_conditioned_severity(
        image_severity    = image_sev,
        outbreak_score    = ob_score,
        neighbor_risk     = nbr_risk,
        temporal_momentum = momentum,
        ndvi_depletion    = ndvi_dep,
    )

    # Summarise adjacent cells (ring 1 — 8 neighbours, filter empty)
    adj_risks = []
    for ncid in adjacent_cells(lat, lon, radius=1):
        ns = index.get(ncid, [])
        if not ns:
            continue
        ns_st = _cell_stats(ns)
        nlat, nlon = cell_center(ncid)
        adj_risks.append({
            "cell_id":          ncid,
            "lat":              nlat,
            "lon":              nlon,
            "avg_severity":     ns_st["avg_severity"],
            "scan_count":       ns_st["count"],
            "dominant_disease": ns_st["dominant_disease"],
            "distance_km":      round(haversine_km(lat, lon, nlat, nlon), 1),
        })
    adj_risks.sort(key=lambda x: -x["avg_severity"])

    return {
        # ── Identity ─────────────────────────────────────────────────────
        "cell_id":             cid,
        "lat":                 round(lat, 6),
        "lon":                 round(lon, 6),
        "generated_at":        datetime.now(timezone.utc).isoformat(),

        # ── Cell-level disease aggregates ─────────────────────────────────
        "cell_scan_count":     cell_st["count"],
        "cell_avg_severity":   cell_st["avg_severity"],
        "cell_max_severity":   cell_st["max_severity"],
        "cell_disease_density":cell_st["disease_density"],
        "cell_recent_count":   cell_st["recent_count"],
        "dominant_disease":    cell_st["dominant_disease"],
        "dominant_crop":       cell_st["dominant_crop"],

        # ── Geo / temporal context ────────────────────────────────────────
        "neighbor_risk":       round(nbr_risk, 4),
        "temporal_momentum":   round(momentum, 4),
        "ndvi_proxy":          round(1.0 - ndvi_dep, 4),   # 1=healthy, 0=depleted
        "ndvi_depletion":      round(ndvi_dep, 4),
        "adjacent_cells":      adj_risks[:6],

        # ── Spread metrics ────────────────────────────────────────────────
        "outbreak_score":      round(ob_score,    4),
        "spread_velocity":     round(spd_vel,     4),
        "future_spread":       round(future_spd,  4),

        # ── Composite severity (primary output) ───────────────────────────
        "image_severity":            round(image_sev, 2),
        "geo_conditioned_severity":  geo_cond_sev,
        "geo_severity_level": (
            "Critical" if geo_cond_sev >= 60 else
            "High"     if geo_cond_sev >= 35 else
            "Moderate" if geo_cond_sev >= 15 else "Low"
        ),
    }


def enrich_with_spatial_context(lat: float, lon: float,
                                  pipeline_result: dict) -> dict:
    """
    Enrich a live pipeline result dict with full spatial context.
    Called from pipeline.py Phase 1 after geo_predict.

    Injects: cell_id, geo_conditioned_severity, geo_severity_level,
             ndvi_proxy, ndvi_depletion, neighbor_risk, temporal_momentum,
             adjacent_cells, cell_disease_density
    """
    try:
        spatial = get_spatial_record(lat, lon, scan_result=pipeline_result)
        pipeline_result["cell_id"]                  = spatial["cell_id"]
        pipeline_result["geo_conditioned_severity"] = spatial["geo_conditioned_severity"]
        pipeline_result["geo_severity_level"]        = spatial["geo_severity_level"]
        pipeline_result["ndvi_proxy"]               = spatial["ndvi_proxy"]
        pipeline_result["ndvi_depletion"]           = spatial["ndvi_depletion"]
        pipeline_result["neighbor_risk"]            = spatial["neighbor_risk"]
        pipeline_result["temporal_momentum"]        = spatial["temporal_momentum"]
        pipeline_result["adjacent_cells"]           = spatial["adjacent_cells"]
        pipeline_result["cell_disease_density"]     = spatial["cell_disease_density"]
    except Exception as e:
        logger.warning(f"enrich_with_spatial_context failed: {e}")
    return pipeline_result


# ══════════════════════════════════════════════════════════════════════════════
# AGGREGATE SUMMARIES (used by heatmap + hotspot APIs)
# ══════════════════════════════════════════════════════════════════════════════

def get_all_cell_summaries() -> list:
    """
    Return a compound-risk summary for every grid cell that has scan data.
    Sorted descending by compound risk score.
    """
    index   = _get_grid_index()
    results = []
    for cid, cell_scans in index.items():
        if not cell_scans:
            continue
        stats    = _cell_stats(cell_scans)
        lat, lon = cell_center(cid)
        momentum = _temporal_momentum(cell_scans)
        ndvi     = _ndvi_proxy(cell_scans)

        compound_risk = round(
            stats["avg_severity"] / 100.0 * 0.50 +
            stats["disease_density"]       * 0.30 +
            momentum                       * 0.20,
            4
        )
        results.append({
            "cell_id":          cid,
            "lat":              lat,
            "lon":              lon,
            "scan_count":       stats["count"],
            "avg_severity":     stats["avg_severity"],
            "max_severity":     stats["max_severity"],
            "disease_density":  stats["disease_density"],
            "recent_count":     stats["recent_count"],
            "dominant_disease": stats["dominant_disease"],
            "dominant_crop":    stats["dominant_crop"],
            "temporal_momentum":round(momentum, 4),
            "ndvi_depletion":   round(ndvi, 4),
            "compound_risk":    compound_risk,
        })
    results.sort(key=lambda x: -x["compound_risk"])
    return results


def get_scans_in_bbox(south: float, west: float,
                       north: float, east: float,
                       days: int = 90) -> list:
    """Return all scans within a bounding box and within `days` days old."""
    index   = _get_grid_index()
    results = []
    cutoff  = float(days)
    for cid, cell_scans in index.items():
        try:
            clat, clon = cell_center(cid)
        except Exception:
            continue
        if not (south <= clat <= north and west <= clon <= east):
            continue
        for s in cell_scans:
            if _age_days(s.get("timestamp", "")) <= cutoff:
                results.append(s)
    return results
