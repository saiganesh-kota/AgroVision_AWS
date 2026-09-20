"""
image_store.py — persist uploaded leaf photos somewhere durable
─────────────────────────────────────────────────────────────
The prediction pipeline needs the image on local disk to run inference
(OpenCV / Keras read it by path), so app.py always saves the upload to
UPLOAD_FOLDER first — that part is unchanged.

What changes for AWS: once inference is done, if S3_UPLOADS_BUCKET is set,
the same file is copied to S3 so it survives container restarts/redeploys
and is visible from every instance. The URL returned here is what gets
stored on the scan record and shown in the UI.

Local dev (no S3 configured) keeps working exactly as before — the image
is just served back from /uploads/<filename> by the Flask app itself.
"""

from __future__ import annotations

import os
import logging

logger = logging.getLogger(__name__)

S3_UPLOADS_BUCKET        = os.getenv("S3_UPLOADS_BUCKET", "")
AWS_REGION               = os.getenv("AWS_REGION", "ap-south-1")
CLOUDFRONT_UPLOADS_DOMAIN = os.getenv("CLOUDFRONT_UPLOADS_DOMAIN", "")  # optional CDN in front of the bucket

_CONTENT_TYPES = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg",
    "png": "image/png", "webp": "image/webp",
}

_s3_client = None


def _s3():
    global _s3_client
    if _s3_client is None:
        import boto3
        _s3_client = boto3.client("s3", region_name=AWS_REGION)
    return _s3_client


def persist_upload(local_path: str, filename: str) -> str:
    """
    Upload `local_path` to S3 under uploads/<filename> and return the URL the
    frontend should use. Falls back to the local /uploads/<filename> route
    (served by Flask itself) when S3 isn't configured, or if the upload fails.
    """
    if not S3_UPLOADS_BUCKET:
        return f"/uploads/{filename}"

    key = f"uploads/{filename}"
    ext = filename.rsplit(".", 1)[-1].lower()
    try:
        _s3().upload_file(
            local_path, S3_UPLOADS_BUCKET, key,
            ExtraArgs={"ContentType": _CONTENT_TYPES.get(ext, "application/octet-stream")},
        )
        if CLOUDFRONT_UPLOADS_DOMAIN:
            return f"https://{CLOUDFRONT_UPLOADS_DOMAIN}/{key}"
        return f"https://{S3_UPLOADS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"
    except Exception as e:
        logger.error(f"S3 upload of {filename} failed, using local URL instead: {e}")
        return f"/uploads/{filename}"
