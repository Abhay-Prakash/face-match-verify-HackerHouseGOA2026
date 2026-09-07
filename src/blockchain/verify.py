"""
Phase 6 verification: separate ON_CHAIN and SOURCE checks.

ON_CHAIN: verifyHash() alone — proves the hash exists on-chain (FOUND/MISSING)
and returns the on-chain storage timestamp from the contract Record.
SOURCE: re-fetch matched_image_source_url, rebuild payload reusing the original
canonical timestamp and face_distance from match_result.json (never
recomputed), recompute only matched_image_hash, compare hashes
(MATCH/NO MATCH/UNVERIFIABLE).
"""

import requests

from src.blockchain.chain_config import get_web3, payload_hash_to_bytes32, require_env
from src.blockchain.contract.compile import load_artifact
from src.blockchain.hasher import build_canonical_payload, hash_payload, sha256_bytes
from src.blockchain.upload import _get_contract


def verify_on_chain(
    payload_hash_hex: str,
    rpc_url: str | None = None,
    contract_address: str | None = None,
) -> dict:
    """
    ON_CHAIN HASH VERIFICATION — calls verifyHash() only.
    Does not inspect the live source image. Returns FOUND/MISSING plus the
    on-chain Record timestamp when the hash exists.
    """
    rpc_url = rpc_url or require_env("RPC_URL")
    contract_address = contract_address or require_env("CONTRACT_ADDRESS")

    w3 = get_web3(rpc_url)
    contract = _get_contract(w3, contract_address)
    hash_bytes32 = payload_hash_to_bytes32(payload_hash_hex)
    exists, on_chain_timestamp = contract.functions.verifyHash(hash_bytes32).call()

    return {
        "check": "ON_CHAIN",
        "result": "FOUND" if exists else "MISSING",
        "on_chain_timestamp": on_chain_timestamp if exists else None,
        "payload_hash": payload_hash_hex.lower().removeprefix("0x"),
        "contract_address": contract_address,
    }


def verify_source(match_result: dict) -> dict:
    """
    SOURCE RE-VERIFICATION — re-fetch the matched image and compare hashes.

    Invariant: timestamp and face_distance are taken verbatim from
    match_result["canonical_payload"]. Only matched_image_hash is recomputed
    from freshly downloaded image bytes.
    """
    if match_result.get("status") != "match":
        return {
            "check": "SOURCE",
            "result": "UNVERIFIABLE",
            "reason": "no_match_recorded",
        }

    canonical = match_result.get("canonical_payload")
    original_hash = match_result.get("payload_hash")
    matched_url = match_result.get("match", {}).get("matched_image_source_url")

    if not canonical or not original_hash or not matched_url:
        return {
            "check": "SOURCE",
            "result": "UNVERIFIABLE",
            "reason": "incomplete_match_result",
        }

    try:
        resp = requests.get(matched_url, timeout=15)
        resp.raise_for_status()
        image_bytes = resp.content
    except Exception as exc:
        return {
            "check": "SOURCE",
            "result": "UNVERIFIABLE",
            "reason": f"source_unreachable: {exc}",
            "matched_image_source_url": matched_url,
            "original_payload_hash": original_hash,
        }

    recomputed_image_hash = sha256_bytes(image_bytes)
    payload = build_canonical_payload(
        source_url=canonical["source_url"],
        matched_image_hash=recomputed_image_hash,
        face_distance=canonical["face_distance"],
        timestamp=canonical["timestamp"],
    )
    recomputed_hash = hash_payload(payload)

    if recomputed_hash == original_hash:
        result = "MATCH"
    else:
        result = "NO MATCH"

    return {
        "check": "SOURCE",
        "result": result,
        "original_payload_hash": original_hash,
        "recomputed_payload_hash": recomputed_hash,
        "original_matched_image_hash": canonical["matched_image_hash"],
        "recomputed_matched_image_hash": recomputed_image_hash,
        "matched_image_source_url": matched_url,
        "reused_timestamp": canonical["timestamp"],
        "reused_face_distance": canonical["face_distance"],
    }


def verify_all(match_result: dict) -> dict:
    """
    Run both ON_CHAIN and SOURCE verification. ON_CHAIN is always attempted
    when payload_hash is present; SOURCE runs independently so an
    UNVERIFIABLE source still reports the on-chain outcome.
    """
    payload_hash = match_result.get("payload_hash")
    if not payload_hash:
        return {
            "on_chain_verification": {"check": "ON_CHAIN", "result": "MISSING", "reason": "no_payload_hash"},
            "source_verification": verify_source(match_result),
        }

    on_chain = verify_on_chain(payload_hash)
    source = verify_source(match_result)

    return {
        "payload_hash": payload_hash,
        "on_chain_verification": on_chain,
        "source_verification": source,
    }
