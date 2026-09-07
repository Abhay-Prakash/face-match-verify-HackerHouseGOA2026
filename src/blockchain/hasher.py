"""
Canonical hash payload - the single source of truth used identically by
both upload.py (on submission) and verify.py (on SOURCE re-verification).

The canonical field "face_distance" holds the normalized Euclidean distance
from src/face/encode.py face_distance() — LOWER is a closer match.
"""

import hashlib
import json


def normalize_face_distance(raw_distance: float) -> str:
    """
    Deterministic serialization of the face distance value.
    Invariant #1: normalized ONCE, here, at the point the distance is turned
    into payload data - never re-derived from a raw float elsewhere, and
    never serialized as a raw float into the canonical payload (raw floats
    are not guaranteed to serialize identically across runs/platforms).
    """
    return f"{round(raw_distance, 4):.4f}"


def build_canonical_payload(
    source_url: str,
    matched_image_hash: str,
    face_distance: str,
    timestamp: str,
) -> dict:
    """
    Build the canonical payload dict. face_distance must already be the
    normalized string form (e.g. "0.5002") - use normalize_face_distance()
    to produce it. This function does not re-normalize, so upload.py and
    verify.py both pass through the exact same string value.
    """
    return {
        "source_url": source_url,
        "matched_image_hash": matched_image_hash,
        "face_distance": face_distance,
        "timestamp": timestamp,
    }


def hash_payload(payload: dict) -> str:
    """
    SHA-256 of the payload's sorted-key JSON serialization. This exact
    function is the only place the canonical hash is computed - used
    identically by upload.py and verify.py per invariant #4.
    """
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    """SHA-256 hex digest of raw bytes (used for matched_image_hash)."""
    return hashlib.sha256(data).hexdigest()
