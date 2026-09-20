"""
supplier_engine.py
──────────────────
Finds real nearby agricultural suppliers (pesticide shops, fertiliser stores,
agri-centres) using the Google Places API (Places API - Nearby Search).

Environment variable required:
  GOOGLE_PLACES_API_KEY   → https://console.cloud.google.com/
  (Enable "Places API" in your Google Cloud project)

If the key is not set, an empty list is returned gracefully so the rest of
the pipeline never crashes.
"""

import os
import logging
import requests

logger = logging.getLogger(__name__)

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")

# Radius in metres to search around the given coordinates
SEARCH_RADIUS = 15001   # 15 km — appropriate for rural areas

# Keywords that reliably return agri-shops in India
SEARCH_KEYWORDS = [
    "pesticide shop",
    "agricultural fertilizer store",
    "krishi kendra",
    "agri input center",
]

PLACES_NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
MAX_RESULTS_PER_QUERY = 5
MAX_TOTAL             = 10


def find_nearby_suppliers(lat: float, lon: float, radius: int = 15001) -> list[dict]:
    """
    Query Google Places for agricultural suppliers near (lat, lon).

    Returns a list of dicts:
        [{ name, address, rating, lat, lon, place_id, open_now, types }, ...]

    Returns [] if the API key is not configured or the request fails.
    """
    if not GOOGLE_PLACES_API_KEY:
        logger.warning("GOOGLE_PLACES_API_KEY not set — skipping supplier lookup.")
        return []

    seen_ids: set = set()
    results: list = []

    for keyword in SEARCH_KEYWORDS:
        if len(results) >= MAX_TOTAL:
            break
        try:
            params = {
                "location": f"{lat},{lon}",
                "radius":   radius,
                "keyword":  keyword,
                "key":      GOOGLE_PLACES_API_KEY,
            }
            resp = requests.get(PLACES_NEARBY_URL, params=params, timeout=8)
            resp.raise_for_status()
            data = resp.json()

            if data.get("status") not in ("OK", "ZERO_RESULTS"):
                logger.warning(f"Places API status: {data.get('status')} for keyword '{keyword}'")
                continue

            for place in data.get("results", [])[:MAX_RESULTS_PER_QUERY]:
                pid = place.get("place_id", "")
                if pid in seen_ids:
                    continue
                seen_ids.add(pid)

                geom  = place.get("geometry", {}).get("location", {})
                hours = place.get("opening_hours", {})

                results.append({
                    "name":     place.get("name", "Unknown"),
                    "address":  place.get("vicinity", ""),
                    "rating":   float(place.get("rating", 0.0)),
                    "lat":      float(geom.get("lat", lat)),
                    "lon":      float(geom.get("lng", lon)),
                    "place_id": pid,
                    "open_now": hours.get("open_now"),
                    "types":    place.get("types", []),
                })

                if len(results) >= MAX_TOTAL:
                    break

        except requests.exceptions.Timeout:
            logger.warning(f"Places API timeout for keyword '{keyword}'")
        except Exception as exc:
            logger.warning(f"Places API error for keyword '{keyword}': {exc}")

    # Sort by rating descending, then by distance (approximate via lat/lon delta)
    results.sort(key=lambda x: -x["rating"])
    return results
