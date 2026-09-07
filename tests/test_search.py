"""
Phase 3 tests: domain allowlist filtering + per-candidate face
re-verification. Uses real downloadable images (not fabricated bytes) so
the download/decode/encode/distance path is genuinely exercised.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.face.encode import encode_largest_face_from_path
from src.search.match_finder import filter_to_allowed_domains, find_best_match

CALIB_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "calibration", "threshold_samples")

# Real, currently-live raw-GitHub image URLs (not social-domain, used here
# only to exercise the download+encode path with genuine bytes).
OBAMA_URL = "https://raw.githubusercontent.com/ageitgey/face_recognition/master/examples/obama.jpg"
ALEX_URL = "https://raw.githubusercontent.com/ageitgey/face_recognition/master/examples/alex-lacamoire.png"
DEAD_URL = "https://raw.githubusercontent.com/ageitgey/face_recognition/master/examples/does-not-exist.jpg"


def test_domain_allowlist_filters_correctly():
    candidates = [
        {"link": "https://www.instagram.com/p/abc123/", "thumbnail": OBAMA_URL},
        {"link": "https://1000logos.net/obama-logo/", "thumbnail": OBAMA_URL},
        {"link": "https://pixabay.com/photos/xyz/", "thumbnail": OBAMA_URL},
        {"link": "https://x.com/someuser/status/1", "thumbnail": OBAMA_URL},
    ]
    kept = filter_to_allowed_domains(candidates)
    kept_links = {c["link"] for c in kept}
    assert kept_links == {
        "https://www.instagram.com/p/abc123/",
        "https://x.com/someuser/status/1",
    }
    print(f"PASS: domain allowlist kept {len(kept)}/{len(candidates)} candidates")


def test_no_qualifying_domain_returns_no_qualifying_post():
    candidates = [
        {"link": "https://1000logos.net/obama-logo/", "thumbnail": OBAMA_URL},
        {"link": "http://randomsite.com/x", "thumbnail": OBAMA_URL},
    ]
    input_encoding = encode_largest_face_from_path(os.path.join(CALIB_DIR, "obama_480p.jpg"))
    result = find_best_match(candidates, input_encoding)
    assert result["status"] == "no_qualifying_post"
    print("PASS: non-allowlisted-only candidates -> no_qualifying_post")


def test_genuine_face_match_against_real_downloaded_image():
    # Input: a known Obama photo. Candidate: a DIFFERENT real Obama photo,
    # hosted on a real URL, labeled as if from an allowlisted domain.
    input_encoding = encode_largest_face_from_path(os.path.join(CALIB_DIR, "obama_480p.jpg"))
    candidates = [
        {"link": "https://www.instagram.com/p/fake_but_allowlisted_domain/", "thumbnail": OBAMA_URL},
    ]
    result = find_best_match(candidates, input_encoding)
    assert result["status"] == "match"
    assert result["best_match"]["face_distance"] <= 0.53
    print(f"PASS: genuine match found, distance={result['best_match']['face_distance']:.4f}")


def test_genuine_non_match_against_real_downloaded_image():
    # Input: Obama. Candidate image: a different real person (Alex).
    input_encoding = encode_largest_face_from_path(os.path.join(CALIB_DIR, "obama_480p.jpg"))
    candidates = [
        {"link": "https://www.instagram.com/p/fake_but_allowlisted_domain/", "thumbnail": ALEX_URL},
    ]
    result = find_best_match(candidates, input_encoding)
    assert result["status"] == "no_confident_match"
    print("PASS: genuine non-match correctly rejected as no_confident_match")


def test_dead_image_url_is_skipped_not_fatal():
    input_encoding = encode_largest_face_from_path(os.path.join(CALIB_DIR, "obama_480p.jpg"))
    candidates = [
        {"link": "https://www.instagram.com/p/dead_link/", "thumbnail": DEAD_URL},
        {"link": "https://www.instagram.com/p/live_link/", "thumbnail": OBAMA_URL},
    ]
    result = find_best_match(candidates, input_encoding)
    assert result["status"] == "match"
    assert len(result["skipped_candidates"]) == 1
    assert "download_failed" in result["skipped_candidates"][0]["reason"]
    print("PASS: dead image URL skipped with logged reason, pipeline continued to next candidate")


if __name__ == "__main__":
    test_domain_allowlist_filters_correctly()
    test_no_qualifying_domain_returns_no_qualifying_post()
    test_genuine_face_match_against_real_downloaded_image()
    test_genuine_non_match_against_real_downloaded_image()
    test_dead_image_url_is_skipped_not_fatal()
    print("\nAll Phase 3 tests passed.")
