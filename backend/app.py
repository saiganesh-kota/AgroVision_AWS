from datetime import datetime
import os, uuid, logging, requests, csv, json as _json, warnings
# Suppress sklearn version mismatch warnings — models were saved on a slightly
# different sklearn version. They still function correctly.
# To permanently fix: re-save all .pkl models on the same sklearn version as
# the server (pip show scikit-learn to check current version).
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import db
import image_store
from model_loader import ensure_models

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Pull model weights from S3 if they aren't already on disk (no-op locally
# when MODELS_S3_BUCKET isn't set — see model_loader.py).
ensure_models()

app = Flask(__name__)
CORS(app, origins="*")

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

# ── API Keys ──────────────────────────────────────────────────────────────────
GEMINI_API_KEY        = os.getenv("GEMINI_API_KEY", "")
OPENWEATHER_API_KEY   = os.getenv("OPENWEATHER_API_KEY", "")
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")

# ── Gemini client (cached — created once, not per-request) ────────────────────
_gemini_client = None
def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None and GEMINI_API_KEY:
        try:
            from google import genai as _genai
            _gemini_client = _genai.Client(api_key=GEMINI_API_KEY)
        except Exception as e:
            logger.error(f"Gemini client init failed: {e}")
    return _gemini_client

# Models verified to work with this API key (tested 2026-07-27).
# gemini-2.0-flash has 0 free-tier quota remaining — excluded.
# gemini-1.5-flash is 404 (removed from API) — excluded.
# Order: best quality first, with reliable fallbacks.
GEMINI_MODELS = [
    "gemini-2.5-flash",         # primary — works reliably
    "gemini-3.6-flash",         # newest fallback
    "gemini-3-flash-preview",   # additional fallback
]


def allowed_file(fn):
    return "." in fn and fn.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_user_id() -> str:
    """Read per-user ID from X-User-Id header sent by the frontend Axios interceptor.
    Falls back to 'anonymous' so the app still works without auth."""
    return request.headers.get("X-User-Id", "anonymous").strip() or "anonymous"




# ── Lazy loaders ──────────────────────────────────────────────────────────────
_pipeline = None
def get_pipeline():
    global _pipeline
    if _pipeline is None:
        from pipeline import full_pipeline
        _pipeline = full_pipeline
    return _pipeline

_supplier_engine = None
def get_supplier_engine():
    global _supplier_engine
    if _supplier_engine is None:
        from supplier_engine import find_nearby_suppliers
        _supplier_engine = find_nearby_suppliers
    return _supplier_engine


@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# ══════════════════════════════════════════════════════════
#  PREDICT  (Patent Feature VIII — Automated Decision Pipeline)
# ══════════════════════════════════════════════════════════
@app.route("/predict", methods=["POST"])
def predict():
    try:
        image_path = None
        uploaded_filename = None  # set only when this request saved a fresh file
        if "image" in request.files:
            file = request.files["image"]
            if file and allowed_file(file.filename):
                ext        = file.filename.rsplit(".", 1)[1].lower()
                fn         = f"{uuid.uuid4().hex}.{ext}"
                image_path = os.path.join(UPLOAD_FOLDER, fn)
                file.save(image_path)
                uploaded_filename = fn
        elif request.is_json:
            image_path = request.get_json().get("image_path")

        if not image_path:
            return jsonify({"error": "No image provided"}), 400

        body = request.get_json() if request.is_json else request.form.to_dict()
        def sf(k, d=0.0):
            try:    return float(body.get(k, d))
            except: return d

        temperature = sf("temperature", 25.0)
        humidity    = sf("humidity",    60.0)
        ph          = sf("ph",          6.5)
        rainfall    = sf("rainfall",    100.0)
        lat         = sf("lat",         20.5)
        lon         = sf("lon",         78.9)
        field_id    = body.get("field_id") or None
        # ── crop_type: accepted from frontend, passed into pipeline ──────────
        crop_type   = body.get("crop_type") or body.get("crop") or None

        logger.info(f"Pipeline: temp={temperature} hum={humidity} ph={ph} lat={lat} lon={lon} crop={crop_type}")
        result = get_pipeline()(image_path, temperature, humidity, ph, rainfall, lat, lon, crop_type=crop_type)

        if result.get("status") in ("not_a_leaf", "model_error"):
            return jsonify(result), 422

        # Nearby suppliers
        try:
            result["nearby_suppliers"] = get_supplier_engine()(lat, lon)
        except Exception as e:
            logger.warning(f"Supplier lookup failed: {e}")
            result["nearby_suppliers"] = []

        # Persist the photo somewhere durable (S3, if configured) now that
        # inference is done with it — App Runner's local disk doesn't
        # survive restarts/redeploys. Falls back to the local /uploads
        # route automatically when S3 isn't configured.
        img_url = (image_store.persist_upload(image_path, uploaded_filename)
                   if uploaded_filename else
                   (f"/uploads/{os.path.basename(image_path)}" if image_path else None))

        scan = db.save_scan(result, image_path, lat=lat, lon=lon, field_id=field_id,
                             user_id=get_user_id(), image_url=img_url)
        return jsonify({**result, "image_path": img_url, "scan": {"id": scan["id"], "timestamp": scan["timestamp"]}})

    except Exception as e:
        logger.exception("Pipeline error")
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════
#  FEEDBACK LOOP  (Patent Feature VII)
# ══════════════════════════════════════════════════════════
@app.route("/feedback", methods=["POST"])
def receive_feedback():
    try:
        body      = request.get_json() or {}
        scan_id   = body.get("scan_id", "unknown")
        correct   = bool(body.get("correct", True))
        timestamp = body.get("timestamp") or datetime.now().astimezone().isoformat()

        scan = db.get_scan_by_id(scan_id) or {}
        r    = scan.get("result") or {}
        lat  = float(scan.get("lat") or body.get("lat", 20.5))
        lon  = float(scan.get("lon") or body.get("lon", 78.9))

        temp         = float(r.get("temperature", body.get("temperature", 25.0)))
        humidity     = float(r.get("humidity",    body.get("humidity",    60.0)))
        ph           = float(r.get("ph",          body.get("ph",          6.5)))
        soil_moisture= float(r.get("soil_moisture", 0.0))
        severity     = float(r.get("severity", 0.0))
        risk         = r.get("risk", "Low")
        predicted    = r.get("recommendation_action", "monitor")
        actual       = predicted if correct else body.get("actual_action", "other")

        try:
            from feedback_collector import save_feedback
            save_feedback(temp, humidity, ph, soil_moisture, severity, risk, predicted, actual)
        except Exception as e:
            logger.warning(f"feedback_collector failed: {e}")
            fb_path = os.path.join(BASE_DIR, "feedback_data.csv")
            row = {
                "temperature": temp, "humidity": humidity, "ph": ph,
                "soil_moisture": soil_moisture, "severity": severity,
                "risk": risk, "prediction": predicted, "actual": actual,
                "correct": int(correct), "lat": lat, "lon": lon,
                "timestamp": timestamp, "scan_id": scan_id,
            }
            write_hdr = not os.path.exists(fb_path)
            with open(fb_path, "a", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(row.keys()))
                if write_hdr: w.writeheader()
                w.writerow(row)

        weights_path = os.path.join(BASE_DIR, "adaptive_weights.json")
        if os.path.exists(weights_path):
            with open(weights_path) as f:
                weights = _json.load(f)
            if predicted in weights:
                lr = 0.08
                if correct:
                    weights[predicted] = min(1.0, weights[predicted] + lr * (1 - weights[predicted]))
                else:
                    weights[predicted] = max(0.1, weights[predicted] - lr * weights[predicted])
                with open(weights_path, "w") as f:
                    _json.dump(weights, f, indent=2)

        return jsonify({
            "status":  "ok",
            "message": "Feedback saved. RL updated. Model will auto-retrain.",
            "action":  predicted,
            "correct": correct,
        })

    except Exception as e:
        logger.exception("Feedback error")
        return jsonify({"error": str(e)}), 500


@app.route("/feedback/stats", methods=["GET"])
def feedback_stats():
    try:
        fb_path = os.path.join(BASE_DIR, "feedback_data.csv")
        if not os.path.exists(fb_path):
            return jsonify({"total": 0, "correct": 0, "accuracy": 0, "weights": {}})
        import pandas as pd
        df = pd.read_csv(fb_path)
        total   = len(df)
        correct = int(df["correct"].sum()) if "correct" in df.columns else 0
        acc     = round(correct / total * 100, 1) if total > 0 else 0
        weights = {}
        wp = os.path.join(BASE_DIR, "adaptive_weights.json")
        if os.path.exists(wp):
            with open(wp) as f:
                weights = _json.load(f)
        retrain_log = []
        log_path = os.path.join(BASE_DIR, "retrain.log")
        if os.path.exists(log_path):
            with open(log_path) as f:
                retrain_log = f.readlines()[-5:]
        return jsonify({"total": total, "correct": correct, "accuracy": acc,
                        "weights": weights, "last_retrain_log": retrain_log})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════
#  GOVERNMENT SCHEMES — moved BEFORE generic routes to avoid shadowing
# ══════════════════════════════════════════════════════════
@app.route("/schemes", methods=["GET"])
def list_schemes():
    try:
        from schemes_data import get_schemes
        crop     = request.args.get("crop")
        state    = request.args.get("state")
        category = request.args.get("category")
        lang     = request.args.get("lang", "en")
        result   = get_schemes(crop, state, category, lang)
        logger.info(f"Schemes returned: {len(result)} items (crop={crop}, state={state})")
        return jsonify(result)
    except Exception as e:
        logger.exception("Schemes error")
        return jsonify({"error": str(e)}), 500

@app.route("/schemes/for-crop", methods=["GET"])
def schemes_for_crop():
    """Returns schemes matched to a detected crop — used by AnalysisPage."""
    try:
        from schemes_data import get_crop_matched_schemes
        crop  = request.args.get("crop", "")
        state = request.args.get("state")
        return jsonify(get_crop_matched_schemes(crop, state))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/schemes/meta", methods=["GET"])
def schemes_meta():
    try:
        from schemes_data import get_categories, get_states
        return jsonify({"categories": get_categories(), "states": get_states()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/contacts", methods=["GET"])
def list_contacts():
    try:
        from schemes_data import get_contacts
        state = request.args.get("state")
        return jsonify(get_contacts(state))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════
#  SUPPLIERS
# ══════════════════════════════════════════════════════════
@app.route("/suppliers")
def suppliers():
    try:
        lat    = float(request.args.get("lat", 20.5))
        lon    = float(request.args.get("lon", 78.9))
        radius = int(request.args.get("radius", 15001))
        return jsonify(get_supplier_engine()(lat, lon, radius))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════
#  DASHBOARD, HISTORY, SCANS, FIELDS, WEATHER
# ══════════════════════════════════════════════════════════
@app.route("/dashboard")
def dashboard():
    try: return jsonify(db.compute_dashboard(request.args.get("field_id"), user_id=get_user_id()))
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/health-trend")
def health_trend():
    try:
        return jsonify(db.compute_health_trend(
            request.args.get("field_id"), int(request.args.get("days", 30))))
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/history")
def history():
    try:
        return jsonify(db.get_scans(int(request.args.get("limit", 100)), request.args.get("field_id"), user_id=get_user_id()))
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/scan/<scan_id>")
def get_scan(scan_id):
    scan = db.get_scan_by_id(scan_id, user_id=get_user_id())
    return jsonify(scan) if scan else (jsonify({"error": "Not found"}), 404)

@app.route("/geo-points")
def geo_points():
    try: return jsonify(db.get_geo_points(user_id=get_user_id()))
    except Exception as e: return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════
#  GEOSPATIAL INTELLIGENCE ENGINE  (Patent Features XII-XIII)
# ══════════════════════════════════════════════════════════════════════════

@app.route("/geo/spatial-record", methods=["GET"])
def geo_spatial_record():
    """
    Full SpatialAgriRecord for a location — associates multimodal agricultural
    data with geographic coordinates: cell stats, neighbor risk, NDVI proxy,
    temporal momentum, and composite geo-conditioned severity.
    """
    try:
        from geo_spatial_engine import get_spatial_record
        lat = float(request.args.get("lat", 20.5))
        lon = float(request.args.get("lon", 78.9))
        return jsonify(get_spatial_record(lat, lon))
    except Exception as e:
        logger.exception("geo/spatial-record error")
        return jsonify({"error": str(e)}), 500


@app.route("/geo/heatmap", methods=["GET"])
def geo_heatmap():
    """
    Heat-map data: compound risk score per 0.1° grid cell within radius_km.
    Frontend renders each cell as a colored transparent circle overlay.
    """
    try:
        from geo_forecast_engine import generate_heatmap
        lat    = float(request.args.get("lat",    20.5))
        lon    = float(request.args.get("lon",    78.9))
        radius = float(request.args.get("radius", 500.0))
        days   = int(request.args.get("days",     30))
        return jsonify(generate_heatmap(lat, lon, radius_km=radius, days=days))
    except Exception as e:
        logger.exception("geo/heatmap error")
        return jsonify({"error": str(e)}), 500


@app.route("/geo/forecast", methods=["GET"])
def geo_forecast():
    """
    7-day geospatial disease spread forecast for a location.
    Uses SIR-inspired cellular automaton with seasonal wind direction bias.
    """
    try:
        from geo_forecast_engine import forecast_zone
        lat      = float(request.args.get("lat",      20.5))
        lon      = float(request.args.get("lon",      78.9))
        days     = int(request.args.get("days",       7))
        humidity = float(request.args.get("humidity", 65.0))
        rainfall = float(request.args.get("rainfall", 80.0))
        return jsonify(forecast_zone(lat, lon, days=days,
                                     humidity=humidity, rainfall=rainfall))
    except Exception as e:
        logger.exception("geo/forecast error")
        return jsonify({"error": str(e)}), 500


@app.route("/geo/disease-hotspots", methods=["GET"])
def geo_disease_hotspots():
    """Top-N disease outbreak hotspots ranked by compound risk score."""
    try:
        from geo_forecast_engine import compute_outbreak_hotspots
        top_n = int(request.args.get("top_n", 10))
        return jsonify(compute_outbreak_hotspots(top_n=top_n))
    except Exception as e:
        logger.exception("geo/disease-hotspots error")
        return jsonify({"error": str(e)}), 500


@app.route("/geo/zone-alerts", methods=["GET"])
def geo_zone_alerts():
    """Structured zone-level disease alerts near a location."""
    try:
        from geo_forecast_engine import generate_zone_alerts
        lat    = float(request.args.get("lat",    20.5))
        lon    = float(request.args.get("lon",    78.9))
        radius = float(request.args.get("radius", 300.0))
        return jsonify(generate_zone_alerts(lat, lon, radius_km=radius))
    except Exception as e:
        logger.exception("geo/zone-alerts error")
        return jsonify({"error": str(e)}), 500

@app.route("/fields", methods=["GET"])
def list_fields(): return jsonify(db.get_fields(user_id=get_user_id()))

@app.route("/fields", methods=["POST"])
def create_field():
    data = request.get_json() or {}
    if not data.get("name"): return jsonify({"error": "name required"}), 400
    return jsonify(db.create_field(data, user_id=get_user_id())), 201

@app.route("/fields/<fid>", methods=["PUT"])
def update_field(fid):
    f = db.update_field(fid, request.get_json() or {})
    return jsonify(f) if f else (jsonify({"error": "Not found"}), 404)

@app.route("/fields/<fid>", methods=["DELETE"])
def delete_field(fid): db.delete_field(fid); return jsonify({"status": "deleted"})

@app.route("/fields/<fid>/data")
def field_data(fid): return jsonify(db.get_field_data(fid))

@app.route("/weather")
def weather():
    lat = request.args.get("lat", "20.5")
    lon = request.args.get("lon", "78.9")
    if not OPENWEATHER_API_KEY:
        import random
        from datetime import date, timedelta
        mock = [{"date": (date.today()+timedelta(days=i)).isoformat(),
                 "temp": 28+random.randint(-4,4), "humidity": 60+random.randint(-10,15),
                 "description": "partly cloudy", "icon": "02d"} for i in range(7)]
        return jsonify({"weather_7d": mock})
    try:
        resp = requests.get(
            f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}"
            f"&appid={OPENWEATHER_API_KEY}&units=metric&cnt=56", timeout=10)
        resp.raise_for_status()
        days = {}
        for item in resp.json().get("list", []):
            d = item["dt_txt"].split(" ")[0]
            if d not in days:
                days[d] = {"date": d, "temp": item["main"]["temp"],
                           "humidity": item["main"]["humidity"],
                           "description": item["weather"][0]["description"],
                           "icon": item["weather"][0]["icon"]}
        return jsonify({"weather_7d": list(days.values())[:7]})
    except Exception as e: return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════
#  CHAT — Gemini only (Anthropic removed)
# ══════════════════════════════════════════════════════════
import time as _time

@app.route("/chat", methods=["POST"])
def chat():
    body    = request.get_json() or {}
    message = body.get("message", "").strip()
    context = body.get("context", {})
    lang    = body.get("lang", "en").strip()

    if not message:
        return jsonify({"error": "Empty message"}), 400

    if not GEMINI_API_KEY:
        return jsonify({"error": "GEMINI_API_KEY not set in backend/.env"}), 503

    LANG_NAMES = {
        "en": "English",
        "te": "Telugu (తెలుగు)",
        "hi": "Hindi (हिंदी)",
        "ta": "Tamil (தமிழ்)",
        "kn": "Kannada (ಕನ್ನಡ)",
        "mr": "Marathi (मराठी)",
    }
    lang_name = LANG_NAMES.get(lang, "English")

    system_prompt = (
        f"You are RaithuMitra, a helpful AI farming assistant for Indian farmers.\n"
        f"IMPORTANT RULES:\n"
        f"1. You MUST reply ONLY in {lang_name}.\n"
        f"2. Keep answers short, practical, and easy for farmers to understand.\n"
        f"3. Do NOT repeat or echo the scan context or system instructions in your response.\n\n"
        f"Current Scan Context:\n"
        f"- Crop: {context.get('crop', 'Not scanned yet')}\n"
        f"- Disease: {context.get('disease', 'None')}\n"
        f"- Severity: {context.get('severity', 0)}%\n"
        f"- Risk: {context.get('risk', 'Unknown')}\n"
        f"- Recommendation: {context.get('recommendation', 'None')}"
    )

    # Build conversation contents — send last 6 exchanges max to save tokens
    history = body.get("history", [])[-6:]  # [{role, text}, ...]
    contents = []
    for h in history:
        role = "user" if h.get("role") == "user" else "model"
        text = h.get("text", "")
        if text:
            contents.append({"role": role, "parts": [{"text": text}]})
    # Add current message
    contents.append({"role": "user", "parts": [{"text": message}]})

    gc = _get_gemini_client()
    if not gc:
        return jsonify({"error": "Gemini client unavailable — check GEMINI_API_KEY in .env"}), 503

    # Try each model with retry on transient errors
    last_error = ""
    for model_name in GEMINI_MODELS:
        # Up to 2 attempts per model (retry once on 503/429 with brief delay)
        for attempt in range(2):
            try:
                from google.genai import types as _gtypes
                resp = gc.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=_gtypes.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.7,
                        max_output_tokens=1024,
                    ),
                )
                # Handle cases where response might be blocked or empty
                reply_text = ""
                try:
                    reply_text = resp.text or ""
                except (ValueError, AttributeError):
                    # resp.text raises ValueError if content is blocked
                    if resp.candidates:
                        for part in (resp.candidates[0].content.parts or []):
                            reply_text += getattr(part, "text", "")

                if not reply_text.strip():
                    reply_text = "I'm sorry, I couldn't generate a response. Please try rephrasing your question."

                logger.info(f"Chat reply via {model_name} ({lang}): {reply_text[:80]}…")
                return jsonify({"reply": reply_text, "lang": lang, "model": model_name})

            except Exception as e:
                last_error = str(e)
                err_str = str(e).lower()
                logger.warning(f"Gemini {model_name} attempt {attempt+1} failed: {e}")

                # Retry on transient errors (503 overload, 429 rate limit)
                if attempt == 0 and ("503" in err_str or "429" in err_str or "unavailable" in err_str or "resource_exhausted" in err_str):
                    _time.sleep(2)  # brief delay before retry
                    continue

                break  # permanent error (404 etc.) — skip to next model

    logger.error(f"All Gemini models failed. Last error: {last_error}")
    # Give user a more helpful error
    if "quota" in last_error.lower() or "resource_exhausted" in last_error.lower():
        return jsonify({"error": "API rate limit reached. Please wait 30 seconds and try again."}), 503
    elif "404" in last_error:
        return jsonify({"error": "AI models unavailable. Please contact support."}), 503
    return jsonify({"error": "Gemini unavailable. Please wait a moment and try again."}), 503



# ══════════════════════════════════════════════════════════
#  SOIL PARAMETERS FROM GPS  (Patent Feature X)
# ══════════════════════════════════════════════════════════
@app.route("/soil-params", methods=["GET"])
def soil_params():
    """
    Fetch real soil parameters (pH, organic carbon, moisture, nitrogen,
    texture) for a GPS location using SoilGrids + Open-Meteo APIs.
    """
    try:
        from soil_api import get_soil_params
        lat = float(request.args.get("lat", 17.38))
        lon = float(request.args.get("lon", 78.47))
        data = get_soil_params(lat, lon)
        return jsonify(data)
    except Exception as e:
        logger.exception("soil-params error")
        return jsonify({"error": str(e)}), 500

# ══════════════════════════════════════════════════════════
#  PEST ALERTS  (Patent Feature IX)
# ══════════════════════════════════════════════════════════
@app.route("/pest-alerts", methods=["GET"])
def pest_alerts():
    """Real-time pest/disease alert forecast for a crop + weather combo."""
    try:
        from pest_alerts import generate_pest_alerts
        crop     = request.args.get("crop", "Wheat")
        temp     = float(request.args.get("temp", 28))
        humidity = float(request.args.get("humidity", 65))
        severity = float(request.args.get("severity", 0))
        geo_risk = request.args.get("geo_risk", "Low")
        alerts   = generate_pest_alerts(crop, temp, humidity, severity, geo_risk)
        return jsonify(alerts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════
#  HEALTH BREAKDOWN  (Detailed score components)
# ══════════════════════════════════════════════════════════
@app.route("/health-breakdown", methods=["POST"])
def health_breakdown_endpoint():
    try:
        from scoring_engine import health_breakdown
        body = request.get_json() or {}
        breakdown = health_breakdown(
            crop       = body.get("crop", ""),
            severity   = float(body.get("severity", 0)),
            soil       = body.get("soil", "Moderate"),
            humidity   = float(body.get("humidity", 60)),
            confidence = float(body.get("confidence", 70)),
        )
        return jsonify(breakdown)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ══════════════════════════════════════════════════════════
#  WEATHER-DISEASE CORRELATION (Patent Feature IX)
# ══════════════════════════════════════════════════════════
@app.route("/weather-risk", methods=["GET"])
def weather_risk():
    try:
        from weather_disease_engine import analyse_weather_risk
        temp     = float(request.args.get("temp",     28))
        humidity = float(request.args.get("humidity", 65))
        rainfall = float(request.args.get("rainfall", 80))
        crop     = request.args.get("crop", "")
        return jsonify(analyse_weather_risk(temp, humidity, rainfall, crop))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════
#  CARBON FOOTPRINT TRACKER (Patent Feature X)
# ══════════════════════════════════════════════════════════
CARBON_DATA = {
    "fungicide":     {"kg_co2_per_acre": 4.2,  "est_cost_per_acre": 350, "category": "Chemical",   "reduction_tip": "Switch to bio-fungicide to save ~60% carbon"},
    "soil_fix":      {"kg_co2_per_acre": 1.1,  "est_cost_per_acre": 120, "category": "Organic",    "reduction_tip": "Compost application sequesters carbon"},
    "ph_correction": {"kg_co2_per_acre": 2.3,  "est_cost_per_acre": 200, "category": "Mineral",    "reduction_tip": "Use agricultural lime — lower carbon than synthetic"},
    "irrigation":    {"kg_co2_per_acre": 0.8,  "est_cost_per_acre": 80,  "category": "Low-carbon", "reduction_tip": "Drip irrigation reduces energy use by 40%"},
    "monitor":       {"kg_co2_per_acre": 0.02, "est_cost_per_acre": 0,   "category": "Zero-input", "reduction_tip": "Monitoring-only is the lowest carbon, zero-cost option"},
}

@app.route("/carbon-footprint", methods=["GET"])
def carbon_footprint():
    action = request.args.get("action", "monitor")
    acres  = float(request.args.get("acres", 1))
    data   = CARBON_DATA.get(action, CARBON_DATA["monitor"])
    total  = round(data["kg_co2_per_acre"] * acres, 3)
    # Compare to baseline (fungicide)
    baseline = CARBON_DATA["fungicide"]["kg_co2_per_acre"] * acres
    saving   = round(max(0.0, baseline - total), 3)
    return jsonify({
        "action":         action,
        "acres":          acres,
        "kg_co2":         total,
        "kg_co2_saved":   saving,
        "est_cost_inr":   round(data["est_cost_per_acre"] * acres, 0),
        "category":       data["category"],
        "reduction_tip":  data["reduction_tip"],
        "carbon_rating":  "A+" if total < 0.1 else "A" if total < 1.5 else "B" if total < 3.0 else "C",
        "all_treatments": {k: round(v["kg_co2_per_acre"] * acres, 3) for k, v in CARBON_DATA.items()},
    })


# ══════════════════════════════════════════════════════════
#  CROP HEALTH CERTIFICATE (Patent Feature XI)
# ══════════════════════════════════════════════════════════
@app.route("/certificate/<scan_id>", methods=["GET"])
def get_certificate(scan_id):
    """Returns structured data for a downloadable crop health certificate."""
    try:
        from db import get_scan_by_id
        scan = get_scan_by_id(scan_id)
        if not scan:
            return jsonify({"error": "Scan not found"}), 404
        r = scan.get("result", {})
        cert = {
            "certificate_id":  f"AGRO-{scan_id[:8].upper()}",
            "scan_id":         scan_id,
            "issued_at":       scan.get("timestamp", ""),
            "crop":            r.get("crop", "Unknown"),
            "disease":         r.get("disease", "Unknown"),
            "health_score":    r.get("health_score", 0),
            "severity":        r.get("severity", 0),
            "severity_level":  r.get("severity_level", "Unknown"),
            "risk":            r.get("risk", "Unknown"),
            "recommendation":  r.get("recommendation", ""),
            "location":        {"lat": scan.get("lat"), "lon": scan.get("lon")},
            "ai_model":        "AgroVision CV Fusion v4",
            "valid_for_days":  7,
            "status":          "Healthy" if r.get("severity", 100) < 10 else "Disease Detected",
        }
        return jsonify(cert)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════
#  STARTUP
# ══════════════════════════════════════════════════════════
def _start_retrain_service():
    # Auto-retrain overwrites the local .pkl model files as feedback comes
    # in. That's fine on a laptop, but on App Runner the container is
    # ephemeral (retrained weights vanish on restart) and can be scaled to
    # multiple instances (each would retrain independently and disagree).
    # Default ON for local dev; set ENABLE_AUTO_RETRAIN=false in production.
    if os.getenv("ENABLE_AUTO_RETRAIN", "true").lower() != "true":
        logger.info("Auto-retrain background service disabled (ENABLE_AUTO_RETRAIN=false).")
        return
    try:
        from retrain_service import start_background_service
        start_background_service()
        logger.info("✅ Auto-retrain background service started.")
    except Exception as e:
        logger.warning(f"Could not start retrain service: {e}")


if __name__ == "__main__":
    _start_retrain_service()
    port  = int(os.getenv("PORT", 5001))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    logger.info(f"AgroVision backend on port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=False)
else:
    _start_retrain_service()
