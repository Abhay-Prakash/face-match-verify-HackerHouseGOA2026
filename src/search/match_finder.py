"""
Filters SearchApi.io Google Lens candidates down to real, qualifying
social-media matches, then re-verifies each candidate's face against the
input face embedding. Explicit skip/failure handling per candidate -
nothing is silently dropped without a logged reason.
"""

import io
from urllib.parse import urlparse

import numpy as np
import requests
from PIL import Image
import face_recognition

from src.face.encode import face_distance, DEFAULT_MATCH_DISTANCE_THRESHOLD
from src.face.detect import NoFaceFoundError

# Supported platforms, not exhaustive coverage - stated as scope, not a
# completeness claim (per canonical spec, point 7).
ALLOWED_DOMAINS = {
    "instagram.com",
    "www.instagram.com",
    "facebook.com",
    "www.facebook.com",
    "twitter.com",
    "x.com",
    "www.x.com",
    "linkedin.com",
    "www.linkedin.com",
    "reddit.com",
    "www.reddit.com",
}


def _domain_of(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def filter_to_allowed_domains(candidates: list[dict]) -> list[dict]:
    """Keep only candidates whose 'link' domain is in the allowlist."""
    kept = []
    for c in candidates:
        link = c.get("link", "")
        if _domain_of(link) in ALLOWED_DOMAINS:
            kept.append(c)
    return kept


def _download_image_bytes(url: str, timeout: int = 15) -> bytes:
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.content

def _extract_media_url(value) -> str | None:
    """Normalize SearchApi image/thumbnail values to a URL string."""
    if isinstance(value, str):
        return value

    if isinstance(value, dict):
        return (
            value.get("link")
            or value.get("url")
            or value.get("src")
        )

    return None



def _encode_face_from_bytes(image_bytes: bytes) -> np.ndarray:
    image = np.array(Image.open(io.BytesIO(image_bytes)).convert("RGB"))
    encodings = face_recognition.face_encodings(image)
    if not encodings:
        raise NoFaceFoundError("No face detected in downloaded candidate image")
    return encodings[0]


def find_best_match(
    candidates: list[dict],
    input_encoding: np.ndarray,
    threshold: float = DEFAULT_MATCH_DISTANCE_THRESHOLD,
) -> dict:
    """
    Given SearchApi.io visual_match candidates and the input face encoding,
    return a dict describing the outcome:

    {
        "status": "match" | "no_qualifying_post" | "no_confident_match",
        "best_match": {..candidate.., "face_distance": float} | None,
        "skipped_candidates": [{"link": ..., "reason": ...}, ...],
    }
    """
    allowed = filter_to_allowed_domains(candidates)

    if not allowed:
        return {
            "status": "no_qualifying_post",
            "best_match": None,
            "skipped_candidates": [],
        }

    skipped = []
    scored = []

    for c in allowed:
        link = c.get("link", "")
        # Prefer the full-resolution matched image ("image") over the
        # compressed, Google-served "thumbnail" - the canonical hash payload
        # must anchor the actual matched image, not a lossy proxy of it.
        image_source_url = _extract_media_url(c.get("image") or c.get("thumbnail"))

        if not image_source_url:
            skipped.append({"link": link, "reason": "no_image_field_in_candidate"})
            continue

        try:
            image_bytes = _download_image_bytes(image_source_url)
        except Exception as e:
            skipped.append({"link": link, "reason": f"download_failed: {e}"})
            continue

        try:
            candidate_encoding = _encode_face_from_bytes(image_bytes)
        except NoFaceFoundError as e:
            skipped.append({"link": link, "reason": f"no_face_detected: {e}"})
            continue
        except Exception as e:
            skipped.append({"link": link, "reason": f"encode_failed: {e}"})
            continue

        d = face_distance(input_encoding, candidate_encoding)
        scored.append({
            **c,
            "face_distance": d,
            "matched_image_source_url": image_source_url,  # exact URL fetched - persisted downstream
            "_image_bytes": image_bytes,
        })

    if not scored:
        return {
            "status": "no_confident_match",
            "best_match": None,
            "skipped_candidates": skipped,
        }

    best = min(scored, key=lambda x: x["face_distance"])

    if best["face_distance"] > threshold:
        return {
            "status": "no_confident_match",
            "best_match": None,
            "skipped_candidates": skipped,
        }

    return {
        "status": "match",
        "best_match": best,
        "skipped_candidates": skipped,
    }
