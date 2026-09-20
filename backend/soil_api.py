"""
soil_api.py — Real Soil Parameters from GPS Location (Patent Feature X)
─────────────────────────────────────────────────────────────────────────
Uses the Open-Meteo API (free, no key needed) to fetch real weather+soil data:
  - Temperature, humidity, rainfall (current weather)
  - Soil temperature at surface
  - pH from SoilGrids (ISRIC)
"""
import logging
import requests

logger = logging.getLogger(__name__)

OPEN_METEO_URL  = "https://api.open-meteo.com/v1/forecast"
SOILGRIDS_URL   = "https://rest.soilgrids.org/soilgrids/v2.0/properties/query"


def get_soil_params(lat: float, lon: float) -> dict:
    """
    Fetch real soil + weather parameters for given coordinates.
    Returns a dict with ph, soil_temperature, humidity, rainfall_estimate.
    Falls back gracefully on any error.
    """
    result = {
        "lat": lat, "lon": lon,
        "source": "estimated",
        "temperature":           None,
        "soil_temperature":      None,
        "humidity":              None,
        "rainfall_estimate":     None,
        "ph":                    None,
        "organic_carbon":        None,
        "nitrogen":              None,
        "soil_type":             "Unknown",
        "clay_content":          None,
        "sand_content":          None,
        "silt_content":          None,
        "suitability":           {},
        "error":                 None,
    }

    # ── 1. Open-Meteo: temperature, humidity, rainfall, soil temp ─────────
    try:
        resp = requests.get(OPEN_METEO_URL, params={
            "latitude":  lat,
            "longitude": lon,
            "current":   "temperature_2m,relative_humidity_2m,precipitation,soil_temperature_0cm",
            "timezone":  "auto",
        }, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        cur  = data.get("current", {})

        if cur.get("temperature_2m") is not None:
            result["temperature"]      = round(float(cur["temperature_2m"]), 1)
        if cur.get("relative_humidity_2m") is not None:
            result["humidity"]         = round(float(cur["relative_humidity_2m"]), 0)
        if cur.get("precipitation") is not None:
            # Convert daily mm to monthly estimate (×30)
            result["rainfall_estimate"] = round(float(cur["precipitation"]) * 30, 1)
        if cur.get("soil_temperature_0cm") is not None:
            result["soil_temperature"] = round(float(cur["soil_temperature_0cm"]), 1)

        result["source"] = "open-meteo"
    except Exception as e:
        logger.warning(f"Open-Meteo error: {e}")

    # ── 2. SoilGrids: pH, organic carbon, nitrogen, texture ──────────────
    try:
        resp = requests.get(SOILGRIDS_URL, params={
            "lon": lon, "lat": lat,
            "property": ["phh2o", "ocd", "nitrogen", "clay", "sand", "silt"],
            "depth":    ["0-5cm"],
            "value":    ["mean"],
        }, timeout=12)
        resp.raise_for_status()
        data = resp.json()

        props = data.get("properties", {}).get("layers", [])
        for layer in props:
            name  = layer.get("name", "")
            unit  = layer.get("unit_measure", {})
            vals  = layer.get("depths", [{}])[0].get("values", {})
            mean  = vals.get("mean")
            if mean is None:
                continue
            d_factor = unit.get("d_factor", 1) or 1
            val = mean / d_factor

            if   name == "phh2o":    result["ph"]             = round(val, 2)
            elif name == "ocd":      result["organic_carbon"] = round(val, 2)
            elif name == "nitrogen": result["nitrogen"]       = round(val, 2)
            elif name == "clay":     result["clay_content"]   = round(val, 1)
            elif name == "sand":     result["sand_content"]   = round(val, 1)
            elif name == "silt":     result["silt_content"]   = round(val, 1)

        if result["source"] == "open-meteo":
            result["source"] = "soilgrids+open-meteo"
        else:
            result["source"] = "soilgrids"

        # Soil texture class from clay/sand
        clay = result["clay_content"] or 0
        sand = result["sand_content"] or 0
        if   clay > 40:               result["soil_type"] = "Clay"
        elif sand > 70:               result["soil_type"] = "Sandy"
        elif clay > 25 and sand < 45: result["soil_type"] = "Clay Loam"
        elif clay < 15 and sand > 50: result["soil_type"] = "Sandy Loam"
        else:                         result["soil_type"] = "Loam"

    except Exception as e:
        logger.warning(f"SoilGrids error: {e}")

    # ── 3. Suitability assessment (uses only pH + organic_carbon) ─────────
    ph = result["ph"]
    oc = result["organic_carbon"]

    result["suitability"] = {
        "rice":      _suit(ph, 5.5, 7.0, oc),
        "wheat":     _suit(ph, 6.0, 7.5, oc),
        "tomato":    _suit(ph, 5.5, 7.0, oc),
        "cotton":    _suit(ph, 6.0, 8.0, oc),
        "groundnut": _suit(ph, 5.5, 6.5, oc),
        "soybean":   _suit(ph, 6.0, 7.0, oc),
    }

    return result


def _suit(ph, ph_min, ph_max, oc) -> str:
    """Simple 3-tier suitability from pH + organic carbon."""
    score = 0
    if ph is not None:
        if ph_min <= ph <= ph_max:                        score += 2
        elif (ph_min - 0.5) <= ph <= (ph_max + 0.5):     score += 1
    if oc is not None:
        if oc > 10:   score += 2
        elif oc > 5:  score += 1

    if   score >= 4: return "Excellent"
    elif score >= 2: return "Moderate"
    else:            return "Poor"
