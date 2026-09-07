"""Face encoding: generate a 128-d embedding for a detected face."""

import numpy as np
import face_recognition

# Calibrated on real data via scripts/calibrate_threshold.py - see that
# script's output for the match/non-match distance distributions this was
# derived from. Not an assumed default.
DEFAULT_MATCH_DISTANCE_THRESHOLD = 0.53

from src.face.detect import load_image, detect_largest_face, NoFaceFoundError


def encode_face(image, face_box: tuple) -> np.ndarray:
    """
    Generate a 128-d embedding for the face at the given bounding box
    (top, right, bottom, left) within the given image (numpy array, RGB).
    """
    encodings = face_recognition.face_encodings(image, known_face_locations=[face_box])
    if not encodings:
        raise NoFaceFoundError("Face location did not yield an encoding")
    return encodings[0]


def encode_largest_face_from_path(path: str) -> np.ndarray:
    """Convenience wrapper: load an image, detect the largest face, encode it."""
    image = load_image(path)
    face_box = detect_largest_face(image)
    return encode_face(image, face_box)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two embeddings, in [-1, 1] (1 = identical direction).
    Kept for reference/tests only - NOT used for match decisions. On real data
    (Phase 1 finding) two different people's face_recognition embeddings scored
    ~0.82 cosine similarity, well above a naive 0.6 cutoff. face_distance()
    below is the metric actually used for matching."""
    a_norm = a / np.linalg.norm(a)
    b_norm = b / np.linalg.norm(b)
    return float(np.dot(a_norm, b_norm))


def face_distance(a: np.ndarray, b: np.ndarray) -> float:
    """
    Euclidean distance between two face embeddings, via face_recognition's
    own face_distance(). Lower = more similar; 0 = identical. This is the
    metric face_recognition is actually calibrated for (its README/tools use
    a ~0.6 distance cutoff as a typical starting threshold) - unlike cosine
    similarity, which runs misleadingly high even for different people on
    this library's embeddings (see Phase 1 finding).
    """
    return float(face_recognition.face_distance([a], b)[0])
