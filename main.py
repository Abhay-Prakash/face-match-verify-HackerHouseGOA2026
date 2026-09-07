"""
End-to-end face-match discovery pipeline.

Phases 1-3: detect/encode input face, SearchApi.io reverse-image search,
           allowlist filter + face re-verification.
Phase 4:    canonical payload + SHA-256 hash.
Phase 5:    storeHash() on Polygon Amoy HashRegistry.
Phase 6:    ON_CHAIN + SOURCE verification.

Writes:
  data/output/match_result.json
  data/output/verification_log.json

Usage:
    python main.py --input data/sample_input/person_a_1.jpg \\
                   --image-url https://example.com/publicly-hosted-same-photo.jpg

SearchApi.io requires a publicly reachable URL for the input image (the `url`
parameter). The local --input file is used for face encoding; --image-url must
point at the same photo hosted somewhere public (GitHub raw, imgur, etc.).
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.blockchain.chain_config import load_project_env
from src.blockchain.hasher import (
    build_canonical_payload,
    hash_payload,
    normalize_face_distance,
    sha256_bytes,
)
from src.blockchain.upload import store_hash
from src.blockchain.verify import verify_all
from src.face.encode import encode_largest_face_from_path
from src.search.match_finder import find_best_match
from src.search.searchapi_client import extract_visual_matches, search_by_image_url

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "output"


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _serialize_match(best: dict) -> dict:
    """Strip non-JSON-serializable fields (_image_bytes, numpy arrays)."""
    return {
        k: v
        for k, v in best.items()
        if k != "_image_bytes" and not k.startswith("_")
    }


def run_pipeline(
    input_path: str,
    image_url: str,
    *,
    skip_blockchain: bool = False,
    skip_verify: bool = False,
) -> dict:
    input_path = str(Path(input_path).resolve())
    print(f"[1/6] Encoding face from {input_path}")
    input_encoding = encode_largest_face_from_path(input_path)

    print(f"[2/6] Reverse-image search via SearchApi.io ({image_url})")
    search_response = search_by_image_url(image_url)
    candidates = extract_visual_matches(search_response)
    print(f"      {len(candidates)} visual match candidates returned")

    print("[3/6] Filtering + face re-verification")
    match_outcome = find_best_match(candidates, input_encoding)
    print(f"      Status: {match_outcome['status']}")
    if match_outcome["skipped_candidates"]:
        print(f"      Skipped {len(match_outcome['skipped_candidates'])} candidate(s)")

    result: dict = {
        "input_image_path": input_path,
        "search_image_url": image_url,
        "status": match_outcome["status"],
        "skipped_candidates": match_outcome["skipped_candidates"],
        "timestamp": _utc_timestamp(),
    }

    if match_outcome["status"] != "match":
        result["match"] = None
        result["canonical_payload"] = None
        result["payload_hash"] = None
        result["blockchain"] = None
        _write_outputs(result, None)
        print("\nNo qualifying match — blockchain upload skipped.")
        return result

    best = match_outcome["best_match"]
    image_bytes = best["_image_bytes"]
    face_distance_str = normalize_face_distance(best["face_distance"])
    matched_image_hash = sha256_bytes(image_bytes)
    source_url = best.get("link", "")

    canonical_payload = build_canonical_payload(
        source_url=source_url,
        matched_image_hash=matched_image_hash,
        face_distance=face_distance_str,
        timestamp=result["timestamp"],
    )
    payload_hash = hash_payload(canonical_payload)

    result["match"] = _serialize_match(best)
    result["canonical_payload"] = canonical_payload
    result["payload_hash"] = payload_hash

    print(f"[4/6] Canonical hash: {payload_hash[:16]}...")

    if skip_blockchain:
        result["blockchain"] = None
        _write_outputs(result, None)
        print("\nBlockchain upload skipped (--skip-blockchain).")
        return result

    print("[5/6] Uploading hash to Polygon Amoy HashRegistry")
    upload_result = store_hash(payload_hash)
    result["blockchain"] = upload_result
    print(f"      Tx: {upload_result['tx_hash']}")
    print(f"      Block: {upload_result['block_number']}")

    verification_log = None
    if not skip_verify:
        print("[6/6] Verifying ON_CHAIN + SOURCE")
        verification_log = verify_all(result)
        on_chain = verification_log["on_chain_verification"]["result"]
        source = verification_log["source_verification"]["result"]
        print(f"      ON_CHAIN: {on_chain}")
        print(f"      SOURCE:   {source}")
    else:
        print("[6/6] Verification skipped (--skip-verify)")

    _write_outputs(result, verification_log)
    return result


def _write_outputs(match_result: dict, verification_log: dict | None) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    match_path = OUTPUT_DIR / "match_result.json"
    match_path.write_text(json.dumps(match_result, indent=2), encoding="utf-8")
    print(f"\nWrote {match_path}")

    if verification_log is not None:
        log = {
            "verified_at": _utc_timestamp(),
            **verification_log,
        }
        log_path = OUTPUT_DIR / "verification_log.json"
        log_path.write_text(json.dumps(log, indent=2), encoding="utf-8")
        print(f"Wrote {log_path}")


def main() -> int:
    load_project_env()
    parser = argparse.ArgumentParser(description="Face-match discovery + blockchain verification pipeline")
    parser.add_argument("--input", required=True, help="Local path to input photo (for face encoding)")
    parser.add_argument(
        "--image-url",
        required=True,
        help="Publicly reachable URL of the same photo (required by SearchApi.io Google Lens)",
    )
    parser.add_argument("--skip-blockchain", action="store_true", help="Skip upload to Amoy (phases 1-4 only)")
    parser.add_argument("--skip-verify", action="store_true", help="Skip phase 6 verification after upload")
    args = parser.parse_args()

    try:
        run_pipeline(
            args.input,
            args.image_url,
            skip_blockchain=args.skip_blockchain,
            skip_verify=args.skip_verify,
        )
        return 0
    except Exception as exc:
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
