"""
leaf_validator.py  — Patent Feature: Leaf-Only Image Gating
────────────────────────────────────────────────────────────
Multi-layer leaf detection. Uses 6 heuristic CV checks + Claude AI vision.

Heuristic checks (fast, local):
  1. Face detection       — Haar cascade hard reject
  2. Straight-line reject — rooms/buildings have strong H/V lines; leaves don't
  3. Sky/blue reject      — outdoor non-plant scenes
  4. Green dominance      — must have meaningful plant-green pixels
  5. Texture variance     — veins/spots give characteristic texture
  6. Edge density         — leaves have distributed fine organic edges

AI vision check (final gate):
  - Sends image to Claude claude-haiku-4-5-20251001 with a strict yes/no prompt
  - Only fires if ALL heuristic checks pass
  - This catches rooms, food, animals, objects that fool colour/edge checks
"""

import base64
import logging
import os

import cv2
import numpy as np
import requests

logger = logging.getLogger(__name__)

# ── Thresholds ────────────────────────────────────────────────────────────────
MIN_GREEN_RATIO     = 0.10   # ≥10% plant-green pixels
MIN_PLANT_RATIO     = 0.13   # green + brown combined
MIN_TEXTURE_VAR     = 60.0   # Laplacian variance
MIN_EDGE_DENSITY    = 0.04   # Canny edge fraction
MIN_SATURATION      = 25.0   # HSV saturation (grey/white objects fail)
MAX_STRAIGHT_RATIO  = 0.55   # max fraction of edges that are straight H/V lines
                              # rooms score ~0.7+, leaves score ~0.2-0.4

FACE_SCALE      = 1.1
FACE_NEIGHBORS  = 8

ANTHROPIC_API   = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"

_FACE_CASCADE = None


# ── Helpers ───────────────────────────────────────────────────────────────────
def _get_face_cascade():
    global _FACE_CASCADE
    if _FACE_CASCADE is None:
        path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        _FACE_CASCADE = cv2.CascadeClassifier(path)
    return _FACE_CASCADE


def _has_face(gray: np.ndarray) -> bool:
    faces = _get_face_cascade().detectMultiScale(
        gray, scaleFactor=FACE_SCALE, minNeighbors=FACE_NEIGHBORS, minSize=(40, 40)
    )
    return len(faces) > 0


def _green_ratio(rgb: np.ndarray) -> float:
    hsv  = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(hsv, np.array([28, 30, 30]), np.array([92, 255, 255]))
    return float(np.sum(mask > 0)) / mask.size


def _brown_yellow_ratio(rgb: np.ndarray) -> float:
    hsv  = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(hsv, np.array([10, 40, 40]), np.array([28, 255, 255]))
    return float(np.sum(mask > 0)) / mask.size


def _texture_variance(rgb: np.ndarray) -> float:
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def _edge_density(rgb: np.ndarray) -> float:
    gray    = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    edges   = cv2.Canny(blurred, 30, 100)
    return float(np.sum(edges > 0)) / edges.size


def _mean_saturation(rgb: np.ndarray) -> float:
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    return float(hsv[:, :, 1].mean())


def _room_line_score(rgb: np.ndarray) -> float:
    """
    Detects obvious room/building characteristics.
    Returns 0.0-1.0. Only clearly man-made scenes (rooms, walls) score > 0.65.
    Real leaf images should score < 0.40.

    Uses: count of long parallel H/V lines AND the pixel coverage they create.
    Rooms have many long parallel walls/shelves. Leaves have at most a few.
    """
    gray    = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges   = cv2.Canny(blurred, 40, 120)
    total_edge_px = float(np.sum(edges > 0))
    if total_edge_px < 100:
        return 0.0

    # Only detect LONG lines (min 45px) to avoid picking up short leaf veins
    lines = cv2.HoughLinesP(
        edges, rho=1, theta=np.pi / 180, threshold=30,
        minLineLength=45, maxLineGap=5
    )
    if lines is None:
        return 0.0

    horiz_count = vert_count = 0
    total_len   = 0.0
    hv_len      = 0.0
    line_mask   = np.zeros_like(edges)

    for line in lines:
        x1, y1, x2, y2 = line[0]
        length = float(np.hypot(x2 - x1, y2 - y1))
        angle  = abs(float(np.degrees(np.arctan2(y2 - y1, x2 - x1))))
        total_len += length

        if angle < 12 or angle > 168:      # horizontal ±12°
            horiz_count += 1
            hv_len += length
            cv2.line(line_mask, (x1, y1), (x2, y2), 255, 2)
        elif 78 < angle < 102:             # vertical ±12°
            vert_count += 1
            hv_len += length
            cv2.line(line_mask, (x1, y1), (x2, y2), 255, 2)

    hv_total = horiz_count + vert_count

    # Need BOTH many lines AND significant pixel coverage to call it a room
    # Rooms: 10+ HV lines covering >15% of edges
    # Leaves: 0-4 HV lines covering <8% of edges
    count_signal  = min(hv_total / 12.0, 1.0)
    pixel_signal  = float(np.sum(line_mask > 0)) / total_edge_px
    combined      = count_signal * 0.6 + pixel_signal * 0.4

    return combined


def _ai_vision_check(image_path: str) -> tuple[bool, str]:
    """
    Final gate: ask Claude Vision whether the image is a plant leaf.
    Returns (is_leaf, reason).
    Falls back to (True, '') if API is unavailable (don't block on network fail).
    """
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set — skipping AI vision check")
            return True, ""

        with open(image_path, "rb") as f:
            raw = f.read()
        b64 = base64.standard_b64encode(raw).decode("utf-8")

        # Detect media type
        ext = os.path.splitext(image_path)[1].lower()
        media_type = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png",  ".webp": "image/webp",
        }.get(ext, "image/jpeg")

        payload = {
            "model":      ANTHROPIC_MODEL,
            "max_tokens": 60,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type":   "image",
                        "source": {"type": "base64", "media_type": media_type, "data": b64},
                    },
                    {
                        "type": "text",
                        "text": (
                            "Look at this image carefully. "
                            "Is it a close-up photo of a single plant leaf or crop leaf "
                            "(including diseased, brown, or yellowed leaves)? "
                            "Answer with ONLY 'YES' or 'NO', nothing else."
                        ),
                    },
                ],
            }],
        }

        resp = requests.post(
            ANTHROPIC_API,
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                     "Content-Type": "application/json"},
            json=payload,
            timeout=3,   # fail fast — 401/timeout both caught and allowed through
        )
        if resp.status_code == 401:
            logger.warning("ANTHROPIC_API_KEY invalid or expired — skipping AI vision check")
            return True, ""
        resp.raise_for_status()
        answer = resp.json()["content"][0]["text"].strip().upper()
        logger.info("AI vision leaf check answer: %s", answer)

        if answer.startswith("YES"):
            return True, ""
        else:
            return False, (
                "This image does not appear to be a plant leaf. "
                "Please upload a clear close-up photo of a crop leaf. "
                "Diseased, brown, or yellowed leaves are supported."
            )

    except requests.exceptions.Timeout:
        logger.warning("AI vision check timed out — allowing image through")
        return True, ""
    except Exception as e:
        logger.warning("AI vision check failed (%s) — allowing image through", e)
        return True, ""


# ── Main validator ────────────────────────────────────────────────────────────
def is_leaf_image(image_path: str) -> tuple[bool, str]:
    """
    Returns (True, '')         if image is a plant leaf.
    Returns (False, reason)    otherwise.
    """
    img = cv2.imread(image_path)
    if img is None:
        return False, "Could not read image file."

    # ── 1. Face detection (requires agreement at BOTH original AND resized
    #      scale before rejecting — a real face is a large, stable pattern
    #      that triggers reliably at both scales; a spurious false-positive
    #      from leaf texture/spot clusters is unlikely to repeat at both) ──
    gray_orig    = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    rgb          = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    rgb          = cv2.resize(rgb, (224, 224))
    gray_s       = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

    if _has_face(gray_orig) and _has_face(gray_s):
        return False, (
            "Human face detected. AgroVision only analyses plant leaf images. "
            "Please upload a clear close-up photo of a crop leaf."
        )

    # ── 2. Straight-line (room/building) detection ─────────────────────────
    room_score = _room_line_score(rgb)
    if room_score > 0.65:
        return False, (
            f"Image appears to contain a room, building, or man-made scene "
            f"(room-line score={room_score:.0%}). "
            "Please upload a clear close-up photo of a crop leaf."
        )

    # ── 3. Sky / blue-dominant rejection ──────────────────────────────────
    hsv       = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    blue_mask = cv2.inRange(hsv, np.array([90, 30, 80]), np.array([135, 255, 255]))
    blue_ratio = float(np.sum(blue_mask > 0)) / blue_mask.size
    green_quick = _green_ratio(rgb)
    if blue_ratio > 0.40 and green_quick < 0.10:
        return False, (
            "Image appears to be sky or an outdoor non-plant scene. "
            "Please upload a clear close-up photo of a crop leaf."
        )

    # ── 4. Green / plant dominance ─────────────────────────────────────────
    green = green_quick
    brown = _brown_yellow_ratio(rgb)
    plant = green + brown * 0.7

    if green < MIN_GREEN_RATIO and plant < MIN_PLANT_RATIO:
        return False, (
            f"Not enough plant-green colour detected "
            f"(green={green:.1%}, plant={plant:.1%}). "
            "Please upload a clear photo of a crop leaf — "
            "brown/yellowed diseased leaves are also supported."
        )

    # ── 5. Texture richness ────────────────────────────────────────────────
    texture = _texture_variance(rgb)
    if texture < MIN_TEXTURE_VAR:
        return False, (
            f"Image appears too plain/uniform to be a leaf "
            f"(texture={texture:.0f}, need ≥{MIN_TEXTURE_VAR:.0f}). "
            "Please upload a close-up leaf photo with visible detail."
        )

    # ── 6. Edge density ────────────────────────────────────────────────────
    edges = _edge_density(rgb)
    if edges < MIN_EDGE_DENSITY:
        return False, (
            f"Insufficient edge/vein detail for a leaf image "
            f"(edge density={edges:.1%}). "
            "Please take a closer photo of the leaf."
        )

    # ── 7. Saturation ──────────────────────────────────────────────────────
    sat = _mean_saturation(rgb)
    if sat < MIN_SATURATION:
        return False, (
            f"Image appears greyscale or poorly lit (saturation={sat:.0f}). "
            "Please use a well-lit colour photo of the crop leaf."
        )

    # ── 8. AI Vision final gate ────────────────────────────────────────────
    return _ai_vision_check(image_path)
