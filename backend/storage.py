"""
storage.py — Pluggable JSON persistence backend for AgroVision AI
────────────────────────────────────────────────────────────────
db.py used to read/write scans_db.json and fields_db.json straight off
local disk. That's fine on a laptop, but on AWS the app runs as a
stateless container (App Runner / ECS Fargate) — local disk is wiped on
every restart or redeploy, and isn't shared across instances.

This module gives db.py two interchangeable backends behind the same
read_json()/write_json() calls:

  STORAGE_BACKEND=local  (default)  → reads/writes a file under BASE_DIR,
                                       exactly like before. Use this for
                                       local dev.
  STORAGE_BACKEND=s3                → reads/writes a JSON object in the
                                       S3 bucket named by S3_DATA_BUCKET.
                                       Use this in production so scan and
                                       field history survives restarts and
                                       is shared across instances.

Nothing else in the codebase needs to change — db.py just calls
storage.read_json(name) / storage.write_json(name, data) instead of
touching files directly.
"""

from __future__ import annotations

import os
import json
import logging

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BACKEND        = os.getenv("STORAGE_BACKEND", "local").lower()
S3_DATA_BUCKET = os.getenv("S3_DATA_BUCKET", "")
AWS_REGION     = os.getenv("AWS_REGION", "ap-south-1")

_s3_client = None


def _s3():
    global _s3_client
    if _s3_client is None:
        import boto3
        _s3_client = boto3.client("s3", region_name=AWS_REGION)
    return _s3_client


def read_json(name: str) -> list:
    """Read a JSON list identified by `name` (e.g. 'scans_db.json')."""
    if BACKEND == "s3" and S3_DATA_BUCKET:
        try:
            obj = _s3().get_object(Bucket=S3_DATA_BUCKET, Key=f"data/{name}")
            return json.loads(obj["Body"].read())
        except _s3().exceptions.NoSuchKey:
            return []
        except Exception as e:
            logger.error(f"S3 read_json({name}) failed, returning []: {e}")
            return []

    path = os.path.join(BASE_DIR, name)
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def write_json(name: str, data: list) -> None:
    """Atomically persist a JSON list under `name`."""
    if BACKEND == "s3" and S3_DATA_BUCKET:
        try:
            _s3().put_object(
                Bucket=S3_DATA_BUCKET,
                Key=f"data/{name}",
                Body=json.dumps(data, indent=2, default=str).encode("utf-8"),
                ContentType="application/json",
            )
            return
        except Exception as e:
            logger.error(f"S3 write_json({name}) failed: {e}")
            return

    path = os.path.join(BASE_DIR, name)
    tmp  = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, default=str)
    os.replace(tmp, path)
