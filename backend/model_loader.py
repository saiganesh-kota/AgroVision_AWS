"""
model_loader.py — fetch model weights from S3 on container startup
────────────────────────────────────────────────────────────────
The models/ folder is ~230MB (CNN + 10 sklearn models). Committing that to
git and rebuilding it into every App Runner deploy is slow and bloats the
repo. Instead: keep the repo lean (models/ is gitignored) and store the
weight files in S3. On startup, ensure_models() downloads whatever's
missing from S3 into the local models/ folder — after that, every existing
module (predict.py, geo_predict.py, etc.) loads them from disk exactly as
before. Nothing about how the models are *used* changes.

Local dev: leave MODELS_S3_BUCKET unset and just keep your models/ folder
on disk like today — ensure_models() becomes a no-op.
"""

from __future__ import annotations

import os
import logging

logger = logging.getLogger(__name__)

BASE_DIR         = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR       = os.path.join(BASE_DIR, "models")
MODELS_S3_BUCKET = os.getenv("MODELS_S3_BUCKET", "")
AWS_REGION       = os.getenv("AWS_REGION", "ap-south-1")

# Everything the pipeline actually loads at inference time. (best_model_old.keras
# is a backup checkpoint, not loaded by any module, so it's deliberately excluded.)
REQUIRED_MODEL_FILES = [
    "best_model.keras",
    "class_names.json",
    "recommend_model.pkl",
    "yield_model.pkl",
    "decision_model.pkl",
    "fusion_model.pkl",
    "geo_model.pkl",
    "geo_spread_model.pkl",
    "outbreak_model.pkl",
    "rl_model.pkl",
    "soil_model.pkl",
    "progression_model.pkl",
    "feedback_model.pkl",
]


def ensure_models() -> None:
    """Download any missing required model file from S3. Safe to call every boot."""
    os.makedirs(MODELS_DIR, exist_ok=True)

    missing = [f for f in REQUIRED_MODEL_FILES
               if not os.path.exists(os.path.join(MODELS_DIR, f))]
    if not missing:
        return

    if not MODELS_S3_BUCKET:
        logger.warning(
            f"Missing model files {missing} and MODELS_S3_BUCKET is not set — "
            "the prediction pipeline will fail until these are placed in models/."
        )
        return

    import boto3
    s3 = boto3.client("s3", region_name=AWS_REGION)
    for filename in missing:
        dest = os.path.join(MODELS_DIR, filename)
        try:
            logger.info(f"Downloading models/{filename} from s3://{MODELS_S3_BUCKET} ...")
            s3.download_file(MODELS_S3_BUCKET, f"models/{filename}", dest)
        except Exception as e:
            logger.error(f"Failed to download models/{filename} from S3: {e}")
