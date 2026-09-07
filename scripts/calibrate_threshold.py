"""
Run against real sample images to pick a genuine face-match distance
threshold, instead of assuming an unvalidated default. Not mocked - uses
real photos in data/calibration/threshold_samples/.

Usage:
    python3 scripts/calibrate_threshold.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.face.encode import encode_largest_face_from_path, face_distance

SAMPLE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "data", "calibration", "threshold_samples"
)

# Known-match pairs: different photos of the SAME real person.
MATCH_PAIRS = [
    ("obama_480p.jpg", "obama_720p.jpg"),
    ("obama_480p.jpg", "obama2.jpg"),
    ("obama_720p.jpg", "obama2.jpg"),
]

# Known-non-match pairs: photos of different real people.
NON_MATCH_PAIRS = [
    ("obama_480p.jpg", "alex.png"),
    ("obama_480p.jpg", "lin.png"),
    ("alex.png", "lin.png"),
]


def path(name):
    return os.path.join(SAMPLE_DIR, name)


def main():
    print("=== Known-MATCH pairs (same person, different photos) ===")
    match_distances = []
    for a, b in MATCH_PAIRS:
        enc_a = encode_largest_face_from_path(path(a))
        enc_b = encode_largest_face_from_path(path(b))
        d = face_distance(enc_a, enc_b)
        match_distances.append(d)
        print(f"  {a} vs {b}: distance = {d:.4f}")

    print("\n=== Known-NON-MATCH pairs (different people) ===")
    non_match_distances = []
    for a, b in NON_MATCH_PAIRS:
        enc_a = encode_largest_face_from_path(path(a))
        enc_b = encode_largest_face_from_path(path(b))
        d = face_distance(enc_a, enc_b)
        non_match_distances.append(d)
        print(f"  {a} vs {b}: distance = {d:.4f}")

    max_match = max(match_distances)
    min_non_match = min(non_match_distances)

    print(f"\nMax distance among known matches:     {max_match:.4f}")
    print(f"Min distance among known non-matches:  {min_non_match:.4f}")

    if max_match < min_non_match:
        suggested = (max_match + min_non_match) / 2
        print(f"\nClean separation. Suggested threshold: {suggested:.4f}")
        print("(distance <= threshold => same-person match)")
    else:
        print(
            "\nWARNING: distributions overlap on this small sample - "
            "pick a threshold conservatively and expand the calibration "
            "set before relying on this for the final demo."
        )


if __name__ == "__main__":
    main()
