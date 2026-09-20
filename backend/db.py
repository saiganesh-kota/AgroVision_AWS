"""
db.py — AgroVision AI Persistence Layer (Schema v2)
────────────────────────────────────────────────────
JSON-file based storage. No external database required.

Changes from v1:
  • user_id on every scan, field, and geo query
  • disease_recommendation stored per scan
  • urgency_class, urgency_class_enc, metafusion fields stored
  • severity_level derived from result if missing (never None)
  • compute_dashboard and compute_health_trend filter by user_id
  • get_geo_points filters by user_id
  • schema_version: 2 on every written record
  • scans_db capped at 1000 (was 500)
  • severity normalized consistently to 0-100 scale

Changes from v2 (thread-safety fix):
  • _DB_LOCK (threading.Lock) guards all read-modify-write operations
    on scans_db.json and fields_db.json.
  • _write() uses atomic rename (write to .tmp then os.replace) so a
    crash mid-write cannot corrupt the live file.
  • This makes concurrent Flask / gunicorn threaded requests safe.
    For multi-process deployments, migrate to SQLite or PostgreSQL.

    
    """

from __future__ import annotations

import os
import uuid
import threading
from datetime import datetime, timezone

import storage

BASE        = os.path.dirname(os.path.abspath(__file__))
SCANS_FILE  = "scans_db.json"
FIELDS_FILE = "fields_db.json"

# One lock covers both stores — simple and sufficient for a single-process
# Flask/gunicorn threaded server. Under storage.py's "s3" backend this also
# protects against interleaved read-modify-write races from concurrent
# requests on the *same* instance; across multiple App Runner instances,
# last-write-wins on S3 still applies (fine for a hackathon-scale demo — a
# DynamoDB backend would be the next step for real concurrent writers).
_DB_LOCK = threading.Lock()


def _read(name):
    """Read JSON list identified by `name`. Returns [] on any error. Caller holds lock."""
    return storage.read_json(name)


def _write(name, data):
    """Persist JSON list identified by `name`. Caller must hold _DB_LOCK."""
    storage.write_json(name, data)


def _severity_level(sev: float) -> str:
    """Derive severity level from numeric severity. Never returns None."""
    if sev < 15:   return "Low"
    if sev < 35:   return "Moderate"
    if sev < 60:   return "High"
    return "Critical"


def _normalize_result(result: dict) -> dict:
    """Ensure every result dict has all required fields at correct types."""
    r = result.copy()
    sev = float(r.get("severity", 0))

    # Severity level — never None
    if not r.get("severity_level"):
        r["severity_level"] = _severity_level(sev)

    # Severity score normalized to 0-1
    if r.get("severity_score", 0) > 1:
        r["severity_score"] = round(sev / 100.0, 4)
    elif not r.get("severity_score"):
        r["severity_score"] = round(sev / 100.0, 4)

    # disease_recommendation — build stub if absent
    if not r.get("disease_recommendation"):
        action = r.get("recommendation_action", "monitor")
        r["disease_recommendation"] = {
            "disease":            r.get("disease", "Unknown"),
            "crop":               r.get("crop", "Unknown"),
            "treatment":          r.get("recommendation"),
            "organic_treatment":  None,
            "recommended_action": action,
            "treatment_name":     str(action).replace("_", " ").title(),
            "urgency":            r.get("urgency_class", "Standard"),
            "severity_pct":       round(sev, 1),
            "model_confidence":   round(
                float(r.get("disease_confidence", 0)) / 100.0
                if float(r.get("disease_confidence", 0)) > 1
                else float(r.get("disease_confidence", 0)), 4
            ),
            "source":             r.get("pipeline_version", "v1"),
        }

    # xai_sentence — build stub if absent
    if not r.get("xai_sentence"):
        urgency = r.get("urgency_class", "Standard")
        disease = r.get("disease", "disease")
        rec     = r.get("recommendation", "treatment")
        r["xai_sentence"] = (
            f"{urgency} urgency for {disease}. "
            f"Action: {rec}. Severity: {round(sev, 1)}%."
        )

    return r


# ══════════════════════════════════════════════════════════════════
# SCANS
# ══════════════════════════════════════════════════════════════════

def get_scans(limit: int = 200, field_id: str = None,
              user_id: str = None) -> list:
    with _DB_LOCK:
        scans = _read(SCANS_FILE)
    if user_id:
        scans = [s for s in scans if s.get("user_id") == user_id]
    if field_id:
        scans = [s for s in scans if s.get("field_id") == field_id]
    return scans[:limit]


def save_scan(result: dict, image_path: str,
              lat=None, lon=None, field_id: str = None,
              user_id: str = None, image_url: str = None) -> dict:

    normalized_result = _normalize_result(result)

    scan = {
        "id":             str(uuid.uuid4()),
        "timestamp":      datetime.now(timezone.utc).isoformat(),
        # image_url wins when the caller already persisted the file
        # somewhere durable (e.g. S3) — see image_store.py.
        "image_path":     image_url or (f"/uploads/{os.path.basename(image_path)}" if image_path else None),
        "crop":           normalized_result.get("crop"),
        "disease":        normalized_result.get("disease"),
        "severity":       float(normalized_result.get("severity", 0)),
        "severity_level": normalized_result.get("severity_level", "Low"),
        "urgency_class":  normalized_result.get("urgency_class", "Standard"),
        "lat":            lat,
        "lon":            lon,
        "field_id":       field_id,
        "field_name":     None,
        "user_id":        user_id,
        "schema_version": 2,
        "result":         normalized_result,
    }

    with _DB_LOCK:
        scans = _read(SCANS_FILE)

        # Attach field name inside lock (fields_db read is cheap)
        if field_id:
            fields = _read(FIELDS_FILE)
            for f in fields:
                if f["id"] == field_id:
                    scan["field_name"] = f["name"]
                    break

        scans.insert(0, scan)
        if len(scans) > 1000:
            scans = scans[:1000]
        _write(SCANS_FILE, scans)

    return scan

from typing import Optional

def get_scan_by_id(scan_id: str, user_id: str = None) -> Optional[dict]:
    with _DB_LOCK:
        scans = _read(SCANS_FILE)
    for s in scans:
        if s.get("id") == scan_id:
            if (user_id and user_id != "anonymous"
                    and s.get("user_id") and s.get("user_id") != user_id):
                return None
            return s
    return None


def patch_scan(scan_id: str, fields: dict) -> dict | None:
    """Update specific fields on an existing scan (e.g. add severity_after)."""
    with _DB_LOCK:
        scans = _read(SCANS_FILE)
        for i, s in enumerate(scans):
            if s.get("id") == scan_id:
                scans[i].update(fields)
                _write(SCANS_FILE, scans)
                return scans[i]
    return None


# ══════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════

def compute_dashboard(field_id: str = None, user_id: str = None) -> dict:
    scans = get_scans(1000, field_id, user_id)
    total = len(scans)

    if total == 0:
        return {
            "total_scans":            0,
            "farm_health_score":      100,
            "average_severity_score": 0.0,
            "critical_count":         0,
            "severity_distribution":  {"Low": 0, "Moderate": 0, "High": 0, "Critical": 0},
            "urgency_distribution":   {"Preventive": 0, "Standard": 0, "Urgent": 0, "Emergency": 0},
            "recent_alerts":          [],
            "recent_scans":           [],
        }

    sev_sum      = 0.0
    crit         = 0
    sev_dist     = {"Low": 0, "Moderate": 0, "High": 0, "Critical": 0}
    urgency_dist = {"Preventive": 0, "Standard": 0, "Urgent": 0, "Emergency": 0}
    alerts       = []

    for s in scans:
        r   = s.get("result") or {}
        sev = float(s.get("severity") or r.get("severity", 0))

        sev_norm = sev / 100.0 if sev > 1 else sev
        sev_sum += sev_norm

        sev_label = (s.get("severity_level")
                     or r.get("severity_level")
                     or _severity_level(sev))
        if sev_label in sev_dist:
            sev_dist[sev_label] += 1
        else:
            sev_dist["Low"] += 1

        urgency = s.get("urgency_class") or r.get("urgency_class", "Standard")
        if urgency in urgency_dist:
            urgency_dist[urgency] += 1

        if r.get("risk") == "High" or sev_norm > 0.6 or urgency in ("Urgent", "Emergency"):
            crit += 1
            rec = ((r.get("disease_recommendation") or {}).get("treatment")
                   or r.get("recommendation"))
            if rec:
                alerts.append({
                    "crop":      s.get("crop") or r.get("crop", "Unknown"),
                    "disease":   s.get("disease") or r.get("disease", "Unknown"),
                    "urgency":   urgency,
                    "alert":     f"{urgency} — {rec}",
                    "timestamp": s.get("timestamp"),
                    "severity":  round(sev, 1),
                })

    avg_sev = sev_sum / total
    health  = max(0, min(100, round((1 - avg_sev) * 100)))

    return {
        "total_scans":            total,
        "farm_health_score":      health,
        "average_severity_score": round(avg_sev, 4),
        "critical_count":         crit,
        "severity_distribution":  sev_dist,
        "urgency_distribution":   urgency_dist,
        "recent_alerts":          alerts[:5],
        "recent_scans":           scans[:8],
    }


def compute_health_trend(field_id: str = None, days: int = 30,
                          user_id: str = None) -> list:
    from collections import defaultdict
    scans = get_scans(1000, field_id, user_id)
    daily = defaultdict(list)

    for s in scans:
        day = (s.get("timestamp") or "")[:10]
        sev = float(s.get("severity")
                    or (s.get("result") or {}).get("severity", 0))
        sev = sev / 100.0 if sev > 1 else sev
        if day:
            daily[day].append(sev)

    trend = []
    for day in sorted(daily.keys())[-days:]:
        vals = daily[day]
        trend.append({
            "day":          day,
            "avg_severity": round(sum(vals) / len(vals), 4),
            "scan_count":   len(vals),
        })
    return trend


# ══════════════════════════════════════════════════════════════════
# FIELDS
# ══════════════════════════════════════════════════════════════════

def get_fields(user_id: str = None) -> list:
    with _DB_LOCK:
        fields = _read(FIELDS_FILE)
    if user_id:
        fields = [f for f in fields if f.get("user_id") == user_id]
    return fields


def create_field(data: dict, user_id: str = None) -> dict:
    field = {
        "id":             str(uuid.uuid4()),
        "created_at":     datetime.now(timezone.utc).isoformat(),
        "name":           data.get("name", "Field"),
        "crop_type":      data.get("crop_type", ""),
        "location":       data.get("location", ""),
        "area_acres":     float(data.get("area_acres", 0) or 0),
        "user_id":        user_id,
        "schema_version": 2,
    }
    with _DB_LOCK:
        fields = _read(FIELDS_FILE)
        fields.append(field)
        _write(FIELDS_FILE, fields)
    return field


def update_field(field_id: str, data: dict, user_id: str = None) -> dict | None:
    with _DB_LOCK:
        fields = _read(FIELDS_FILE)
        for i, f in enumerate(fields):
            if f["id"] == field_id:
                if user_id and f.get("user_id") and f["user_id"] != user_id:
                    return None
                for k in ("name", "crop_type", "location", "area_acres"):
                    if k in data:
                        fields[i][k] = data[k]
                _write(FIELDS_FILE, fields)
                return fields[i]
    return None


def delete_field(field_id: str, user_id: str = None) -> None:
    with _DB_LOCK:
        fields = _read(FIELDS_FILE)
        if user_id:
            fields = [f for f in fields
                      if not (f["id"] == field_id
                              and f.get("user_id") == user_id)]
        else:
            fields = [f for f in fields if f["id"] != field_id]
        _write(FIELDS_FILE, fields)


def get_field_data(field_id: str, user_id: str = None) -> dict:
    return {
        "field_id": field_id,
        "scans":    get_scans(50, field_id, user_id),
    }


# ══════════════════════════════════════════════════════════════════
# GEO POINTS
# ══════════════════════════════════════════════════════════════════

def get_geo_points(user_id: str = None) -> list:
    scans = get_scans(500, user_id=user_id)
    pts   = []
    for s in scans:
        if s.get("lat") and s.get("lon"):
            r  = s.get("result") or {}
            dr = r.get("disease_recommendation") or {}
            pts.append({
                "id":              s["id"],
                "lat":             s["lat"],
                "lon":             s["lon"],
                "crop":            s.get("crop"),
                "disease":         s.get("disease") or r.get("disease"),
                "timestamp":       s.get("timestamp"),
                "severity":        s.get("severity") or r.get("severity", 0),
                "severity_level":  (s.get("severity_level")
                                    or r.get("severity_level", "Low")),
                "urgency_class":   (s.get("urgency_class")
                                    or r.get("urgency_class", "Standard")),
                "geo_risk":        r.get("geo_risk", "Low"),
                "outbreak_score":  r.get("outbreak_score", 0),
                "spread_velocity": r.get("spread_velocity", 0),
                "future_spread":   r.get("future_spread", 0),
                "recommendation":  (dr.get("treatment")
                                    or r.get("recommendation")),
                "user_id":         s.get("user_id"),
                # ── Geospatial Intelligence Engine fields ─────────────────
                "geo_conditioned_severity": r.get("geo_conditioned_severity"),
                "geo_severity_level":        r.get("geo_severity_level"),
                "cell_id":                   r.get("cell_id"),
                "ndvi_proxy":                r.get("ndvi_proxy"),
                "ndvi_depletion":            r.get("ndvi_depletion"),
                "neighbor_risk":             r.get("neighbor_risk"),
                "temporal_momentum":         r.get("temporal_momentum"),
                "cell_disease_density":      r.get("cell_disease_density"),
            })
    return pts
