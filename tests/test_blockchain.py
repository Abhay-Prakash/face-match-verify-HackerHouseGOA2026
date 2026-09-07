"""
Phase 4-6 tests: canonical hashing, contract compilation, SOURCE verification.
"""

import os
import sys

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.blockchain.hasher import (
    normalize_face_distance,
    build_canonical_payload,
    hash_payload,
    sha256_bytes,
)
from src.blockchain.chain_config import payload_hash_to_bytes32
from src.blockchain.contract.compile import compile_contract
from src.blockchain.verify import verify_source

OBAMA_URL = "https://raw.githubusercontent.com/ageitgey/face_recognition/master/examples/obama.jpg"
DEAD_URL = "https://raw.githubusercontent.com/ageitgey/face_recognition/master/examples/does-not-exist.jpg"


def test_normalize_face_distance_produces_fixed_string_form():
    assert normalize_face_distance(0.87) == "0.8700"
    assert normalize_face_distance(0.869999999999999) == "0.8700"
    assert normalize_face_distance(0.60005) == "0.6001" or normalize_face_distance(0.60005) == "0.6000"
    print(f"PASS: normalize_face_distance(0.87) = {normalize_face_distance(0.87)!r}")


def test_floating_point_drift_does_not_change_hash():
    # Simulates invariant #1's exact failure mode: two "equal" floats that
    # differ in raw representation must normalize to the identical string,
    # and therefore produce the identical hash.
    raw_a = 0.8699999999999999
    raw_b = 0.87

    dist_a = normalize_face_distance(raw_a)
    dist_b = normalize_face_distance(raw_b)
    assert dist_a == dist_b, f"Normalization failed to converge: {dist_a!r} vs {dist_b!r}"

    payload_a = build_canonical_payload("https://x.com/p/1", "abc123", dist_a, "2026-09-03T12:00:00Z")
    payload_b = build_canonical_payload("https://x.com/p/1", "abc123", dist_b, "2026-09-03T12:00:00Z")

    hash_a = hash_payload(payload_a)
    hash_b = hash_payload(payload_b)
    assert hash_a == hash_b, "Hashes diverged despite normalized-equal scores"
    print(f"PASS: floating-point drift (0.8699999999999999 vs 0.87) -> identical hash {hash_a[:16]}...")


def test_identical_payload_produces_identical_hash_repeatedly():
    payload = build_canonical_payload(
        "https://instagram.com/p/xyz", "deadbeef", "0.4500", "2026-09-03T10:00:00Z"
    )
    h1 = hash_payload(payload)
    h2 = hash_payload(payload)
    h3 = hash_payload(dict(payload))  # fresh dict, same content, different object
    assert h1 == h2 == h3
    print(f"PASS: identical payload -> identical hash across repeated calls: {h1[:16]}...")


def test_different_content_produces_different_hash():
    p1 = build_canonical_payload("https://x.com/a", "hash1", "0.4500", "2026-09-03T10:00:00Z")
    p2 = build_canonical_payload("https://x.com/a", "hash1", "0.4500", "2026-09-03T10:00:01Z")  # timestamp differs
    assert hash_payload(p1) != hash_payload(p2)
    print("PASS: differing timestamp (only) produces a different hash - provenance-record behavior confirmed")


def test_key_order_does_not_affect_hash():
    # dict literal order shouldn't matter since we sort keys before hashing
    p1 = {
        "source_url": "https://x.com/a",
        "matched_image_hash": "h1",
        "face_distance": "0.5000",
        "timestamp": "2026-09-03T10:00:00Z",
    }
    p2 = {
        "timestamp": "2026-09-03T10:00:00Z",
        "face_distance": "0.5000",
        "matched_image_hash": "h1",
        "source_url": "https://x.com/a",
    }
    assert hash_payload(p1) == hash_payload(p2)
    print("PASS: key insertion order does not affect hash (sort_keys confirmed working)")


def test_sha256_bytes_is_real_sha256():
    import hashlib
    data = b"hello world"
    expected = hashlib.sha256(data).hexdigest()
    assert sha256_bytes(data) == expected
    print(f"PASS: sha256_bytes matches stdlib hashlib: {expected[:16]}...")


def test_compile_contract_produces_abi_and_bytecode():
    artifact = compile_contract()
    assert artifact["abi"]
    assert artifact["bytecode"].startswith("6080") or artifact["bytecode"].startswith("0x")
    assert any(item.get("name") == "storeHash" for item in artifact["abi"])
    verify_fn = next(item for item in artifact["abi"] if item.get("name") == "verifyHash")
    output_names = [out["name"] for out in verify_fn["outputs"]]
    assert output_names == ["exists", "timestamp"]
    print("PASS: HashRegistry.sol compiles with storeHash + verifyHash(exists,timestamp) ABI")


def test_payload_hash_converts_to_bytes32():
    payload = build_canonical_payload("https://x.com/a", "ab" * 32, "0.4500", "2026-09-03T10:00:00Z")
    digest = hash_payload(payload)
    raw = payload_hash_to_bytes32(digest)
    assert len(raw) == 32
    assert raw.hex() == digest
    print("PASS: payload hash -> 32-byte bytes32 conversion")


def _build_sample_match_result(image_url: str, image_hash: str | None = None) -> dict:
    resp = requests.get(image_url, timeout=15)
    resp.raise_for_status()
    image_bytes = resp.content
    matched_image_hash = image_hash or sha256_bytes(image_bytes)
    timestamp = "2026-01-01T00:00:00Z"
    distance = "0.3500"
    canonical = build_canonical_payload(
        "https://www.instagram.com/p/test/",
        matched_image_hash,
        distance,
        timestamp,
    )
    return {
        "status": "match",
        "payload_hash": hash_payload(canonical),
        "canonical_payload": canonical,
        "match": {"matched_image_source_url": image_url},
    }


def test_verify_source_match_when_image_unchanged():
    match_result = _build_sample_match_result(OBAMA_URL)
    outcome = verify_source(match_result)
    assert outcome["result"] == "MATCH"
    assert outcome["reused_timestamp"] == "2026-01-01T00:00:00Z"
    assert outcome["reused_face_distance"] == "0.3500"
    print("PASS: SOURCE verification -> MATCH for unchanged live image")


def test_verify_source_no_match_when_image_hash_differs():
    match_result = _build_sample_match_result(OBAMA_URL, image_hash="0" * 64)
    outcome = verify_source(match_result)
    assert outcome["result"] == "NO MATCH"
    assert outcome["recomputed_payload_hash"] != outcome["original_payload_hash"]
    print("PASS: SOURCE verification -> NO MATCH when stored image hash is wrong")


def test_verify_source_unverifiable_on_dead_url():
    match_result = {
        "status": "match",
        "payload_hash": "abc",
        "canonical_payload": {
            "source_url": "https://www.instagram.com/p/dead/",
            "matched_image_hash": "0" * 64,
            "face_distance": "0.3500",
            "timestamp": "2026-01-01T00:00:00Z",
        },
        "match": {"matched_image_source_url": DEAD_URL},
    }
    outcome = verify_source(match_result)
    assert outcome["result"] == "UNVERIFIABLE"
    assert "source_unreachable" in outcome["reason"]
    print("PASS: SOURCE verification -> UNVERIFIABLE on dead URL")


if __name__ == "__main__":
    test_normalize_face_distance_produces_fixed_string_form()
    test_floating_point_drift_does_not_change_hash()
    test_identical_payload_produces_identical_hash_repeatedly()
    test_different_content_produces_different_hash()
    test_key_order_does_not_affect_hash()
    test_sha256_bytes_is_real_sha256()
    test_compile_contract_produces_abi_and_bytecode()
    test_payload_hash_converts_to_bytes32()
    test_verify_source_match_when_image_unchanged()
    test_verify_source_no_match_when_image_hash_differs()
    test_verify_source_unverifiable_on_dead_url()
    print("\nAll blockchain tests passed.")
