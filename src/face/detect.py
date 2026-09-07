"""Face detection: load an image, detect the largest face, return its bounding box."""

import face_recognition


class NoFaceFoundError(Exception):
    """Raised when no face is detected in the given image."""


def load_image(path: str):
    """Load an image file into an RGB numpy array."""
    return face_recognition.load_image_file(path)


def detect_largest_face(image) -> tuple:
    """
    Detect faces in an image (numpy array, RGB) and return the bounding box
    of the largest one, as (top, right, bottom, left).

    Raises NoFaceFoundError if no face is detected.
    """
    locations = face_recognition.face_locations(image)
    if not locations:
        raise NoFaceFoundError("No face detected in image")

    def area(box):
        top, right, bottom, left = box
        return (bottom - top) * (right - left)

    return max(locations, key=area)


def detect_largest_face_from_path(path: str) -> tuple:
    """Convenience wrapper: load an image from disk and detect its largest face."""
    image = load_image(path)
    return detect_largest_face(image)
