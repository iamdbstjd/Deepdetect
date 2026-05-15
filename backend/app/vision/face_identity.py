from __future__ import annotations

from pathlib import Path
from typing import Protocol

import cv2
import numpy as np

from backend.app.core.config import Settings
from backend.app.vision.detections import Detection


class FaceIdentityError(RuntimeError):
    pass


class PreparedFaceMatcher(Protocol):
    def match_score(self, frame: np.ndarray, detection: Detection) -> float:
        ...

    def is_match(self, frame: np.ndarray, detection: Detection) -> bool:
        ...


class FaceIdentityMatcher(Protocol):
    def prepare(self, reference_image_path: Path) -> PreparedFaceMatcher:
        ...


class DisabledPreparedMatcher:
    def match_score(self, frame: np.ndarray, detection: Detection) -> float:
        return 0.0

    def is_match(self, frame: np.ndarray, detection: Detection) -> bool:
        return False


class DisabledFaceMatcher:
    def prepare(self, reference_image_path: Path) -> PreparedFaceMatcher:
        return DisabledPreparedMatcher()


class HistogramPreparedMatcher:
    def __init__(self, reference_histogram: np.ndarray, threshold: float):
        self.reference_histogram = reference_histogram
        self.threshold = threshold

    def match_score(self, frame: np.ndarray, detection: Detection) -> float:
        height, width = frame.shape[:2]
        box = detection.clipped(width, height, padding_ratio=0.0)
        if not box.is_valid:
            return 0.0
        crop = frame[box.y1 : box.y2, box.x1 : box.x2]
        if crop.size == 0:
            return 0.0
        histogram = _hsv_histogram(crop)
        return float(cv2.compareHist(self.reference_histogram, histogram, cv2.HISTCMP_CORREL))

    def is_match(self, frame: np.ndarray, detection: Detection) -> bool:
        return self.match_score(frame, detection) >= self.threshold


class HistogramFaceMatcher:
    """Development fallback for Phase 3 identity-policy wiring.

    This is not biometric recognition. It only gives us a deterministic matcher
    until a real face embedding model is added.
    """

    def __init__(self, threshold: float = 0.92):
        self.threshold = threshold

    def prepare(self, reference_image_path: Path) -> PreparedFaceMatcher:
        reference = cv2.imread(str(reference_image_path))
        if reference is None or reference.size == 0:
            raise FaceIdentityError(f"cannot read reference image: {reference_image_path}")
        return HistogramPreparedMatcher(_hsv_histogram(reference), self.threshold)


class ArcFacePreparedMatcher:
    def __init__(self, reference_embedding: np.ndarray, net: cv2.dnn.Net, threshold: float):
        self.reference_embedding = reference_embedding
        self.net = net
        self.threshold = threshold

    def match_score(self, frame: np.ndarray, detection: Detection) -> float:
        height, width = frame.shape[:2]
        box = detection.clipped(width, height, padding_ratio=0.08)
        if not box.is_valid:
            return 0.0
        crop = frame[box.y1 : box.y2, box.x1 : box.x2]
        if crop.size == 0:
            return 0.0
        embedding = _arcface_embedding(self.net, crop)
        return _cosine_similarity(self.reference_embedding, embedding)

    def is_match(self, frame: np.ndarray, detection: Detection) -> bool:
        return self.match_score(frame, detection) >= self.threshold


class ArcFaceMatcher:
    def __init__(self, model_path: Path, threshold: float = 0.35):
        self.model_path = model_path
        self.threshold = threshold
        if not model_path.exists():
            raise FaceIdentityError(f"face embedding model not found: {model_path}")
        try:
            self.net = cv2.dnn.readNetFromONNX(str(model_path))
        except cv2.error as exc:
            raise FaceIdentityError(f"cannot load face embedding model: {model_path}") from exc

    def prepare(self, reference_image_path: Path) -> PreparedFaceMatcher:
        reference = cv2.imread(str(reference_image_path))
        if reference is None or reference.size == 0:
            raise FaceIdentityError(f"cannot read reference image: {reference_image_path}")
        return ArcFacePreparedMatcher(
            reference_embedding=_arcface_embedding(self.net, reference),
            net=self.net,
            threshold=self.threshold,
        )


def _hsv_histogram(image: np.ndarray) -> np.ndarray:
    resized = cv2.resize(image, (96, 96), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
    histogram = cv2.calcHist([hsv], [0, 1], None, [32, 32], [0, 180, 0, 256])
    cv2.normalize(histogram, histogram, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
    return histogram


def _arcface_embedding(net: cv2.dnn.Net, image: np.ndarray) -> np.ndarray:
    resized = cv2.resize(image, (112, 112), interpolation=cv2.INTER_AREA)
    blob = cv2.dnn.blobFromImage(
        resized,
        scalefactor=1.0 / 127.5,
        size=(112, 112),
        mean=(127.5, 127.5, 127.5),
        swapRB=True,
        crop=False,
    )
    net.setInput(blob)
    embedding = net.forward().reshape(-1).astype(np.float32)
    norm = np.linalg.norm(embedding)
    if norm == 0:
        return embedding
    return embedding / norm


def _cosine_similarity(left: np.ndarray, right: np.ndarray) -> float:
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    if denominator == 0.0:
        return 0.0
    return float(np.dot(left, right) / denominator)


def build_face_matcher(settings: Settings) -> FaceIdentityMatcher:
    mode = settings.face_matcher_mode.lower()
    if mode == "disabled":
        return DisabledFaceMatcher()
    if mode == "histogram":
        return HistogramFaceMatcher(settings.face_match_threshold)
    if mode == "arcface":
        try:
            if not settings.face_match_model_path:
                raise FaceIdentityError("face embedding model path is not configured")
            return ArcFaceMatcher(settings.face_match_model_path, settings.face_match_threshold)
        except FaceIdentityError:
            return HistogramFaceMatcher(0.92)
    raise FaceIdentityError(
        "unknown face matcher mode: "
        f"{settings.face_matcher_mode}; expected disabled, histogram, or arcface"
    )
