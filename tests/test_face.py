"""
Phase 1 tests: face detection + encoding, run against real sample images
(not mocked). Requires data/sample_input/person_a_1.jpg and person_b_1.jpg
(two genuinely different people) to be present.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.face.detect import detect_largest_face_from_path, NoFaceFoundError
from src.face.encode import encode_largest_face_from_path, cosine_similarity

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sample_input")
PERSON_A = os.path.join(SAMPLE_DIR, "person_a_1.jpg")
PERSON_B = os.path.join(SAMPLE_DIR, "person_b_1.jpg")


def test_detects_face_in_person_a():
    box = detect_largest_face_from_path(PERSON_A)
    top, right, bottom, left = box
    assert bottom > top
    assert right > left
    print(f"PASS: face detected in person_a_1.jpg, box={box}")


def test_detects_face_in_person_b():
    box = detect_largest_face_from_path(PERSON_B)
    top, right, bottom, left = box
    assert bottom > top
    assert right > left
    print(f"PASS: face detected in person_b_1.jpg, box={box}")


def test_same_image_self_similarity_is_near_1():
    # Encoding the same image twice should give near-identical embeddings.
    enc1 = encode_largest_face_from_path(PERSON_A)
    enc2 = encode_largest_face_from_path(PERSON_A)
    sim = cosine_similarity(enc1, enc2)
    print(f"PASS(?): self-similarity (same image, re-encoded) = {sim:.4f}")
    assert sim > 0.99


def test_different_people_similarity_is_lower():
    enc_a = encode_largest_face_from_path(PERSON_A)
    enc_b = encode_largest_face_from_path(PERSON_B)
    sim = cosine_similarity(enc_a, enc_b)
    print(f"PASS(?): cross-person similarity = {sim:.4f}")
    # Genuinely different people should score meaningfully below self-similarity.
    assert sim < 0.90


def test_no_face_found_raises():
    # Build a blank (all-black) image with no face and confirm it raises cleanly.
    import numpy as np
    from src.face.detect import detect_largest_face

    blank = np.zeros((200, 200, 3), dtype=np.uint8)
    try:
        detect_largest_face(blank)
        raise AssertionError("Expected NoFaceFoundError, but none was raised")
    except NoFaceFoundError:
        print("PASS: NoFaceFoundError correctly raised on blank image")


if __name__ == "__main__":
    test_detects_face_in_person_a()
    test_detects_face_in_person_b()
    test_same_image_self_similarity_is_near_1()
    test_different_people_similarity_is_lower()
    test_no_face_found_raises()
    print("\nAll Phase 1 tests passed.")
