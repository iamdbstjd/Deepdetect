from __future__ import annotations

from pathlib import Path
import threading
from typing import Protocol

import cv2
import numpy as np

from backend.app.core.config import Settings
from backend.app.vision.detections import Detection, RegionDetector


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

    def __init__(
        self,
        threshold: float = 0.92,
        reference_detector: RegionDetector | None = None,
    ):
        self.threshold = threshold
        self.reference_detector = reference_detector

    def prepare(self, reference_image_path: Path) -> PreparedFaceMatcher:
        reference = cv2.imread(str(reference_image_path))
        if reference is None or reference.size == 0:
            raise FaceIdentityError(f"cannot read reference image: {reference_image_path}")
        reference = _reference_face_crop(reference, self.reference_detector)
        return HistogramPreparedMatcher(_hsv_histogram(reference), self.threshold)


class ArcFacePreparedMatcher:
    def __init__(
        self,
        reference_embedding: np.ndarray,
        net: cv2.dnn.Net,
        threshold: float,
        lock: threading.RLock,
    ):
        self.reference_embedding = reference_embedding
        self.net = net
        self.threshold = threshold
        self._lock = lock

    def match_score(self, frame: np.ndarray, detection: Detection) -> float:
        height, width = frame.shape[:2]
        box = detection.clipped(width, height, padding_ratio=0.08)
        if not box.is_valid:
            return 0.0
        crop = frame[box.y1 : box.y2, box.x1 : box.x2]
        if crop.size == 0:
            return 0.0
        with self._lock:
            embedding = _arcface_embedding(self.net, crop)
        return _cosine_similarity(self.reference_embedding, embedding)

    def is_match(self, frame: np.ndarray, detection: Detection) -> bool:
        return self.match_score(frame, detection) >= self.threshold


class ArcFaceMatcher:
    def __init__(
        self,
        model_path: Path,
        threshold: float = 0.35,
        reference_detector: RegionDetector | None = None,
    ):
        self.model_path = model_path
        self.threshold = threshold
        self.reference_detector = reference_detector
        if not model_path.exists():
            raise FaceIdentityError(f"face embedding model not found: {model_path}")
        try:
            self.net = cv2.dnn.readNetFromONNX(str(model_path))
        except cv2.error as exc:
            raise FaceIdentityError(f"cannot load face embedding model: {model_path}") from exc
        self._lock = threading.RLock()

    def prepare(self, reference_image_path: Path) -> PreparedFaceMatcher:
        reference = cv2.imread(str(reference_image_path))
        if reference is None or reference.size == 0:
            raise FaceIdentityError(f"cannot read reference image: {reference_image_path}")
        reference = _reference_face_crop(reference, self.reference_detector)
        with self._lock:
            reference_embedding = _arcface_embedding(self.net, reference)
        return ArcFacePreparedMatcher(
            reference_embedding=reference_embedding,
            net=self.net,
            threshold=self.threshold,
            lock=self._lock,
        )


def _hsv_histogram(image: np.ndarray) -> np.ndarray:
    resized = cv2.resize(image, (96, 96), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
    histogram = cv2.calcHist([hsv], [0, 1], None, [32, 32], [0, 180, 0, 256])
    cv2.normalize(histogram, histogram, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
    return histogram


def _reference_face_crop(
    image: np.ndarray,
    detector: RegionDetector | None,
) -> np.ndarray:
    if detector is None:
        return image
    try:
        detections = detector.detect(image)
    except Exception:
        return image
    height, width = image.shape[:2]
    face_boxes = [
        detection.clipped(width, height, padding_ratio=0.08)
        for detection in detections
        if detection.kind == "face"
    ]
    valid_boxes = [box for box in face_boxes if box.is_valid]
    if not valid_boxes:
        return image
    box = max(valid_boxes, key=lambda item: (item.x2 - item.x1) * (item.y2 - item.y1))
    crop = image[box.y1 : box.y2, box.x1 : box.x2]
    return crop if crop.size else image


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


def build_face_matcher(
    settings: Settings,
    reference_detector: RegionDetector | None = None,
) -> FaceIdentityMatcher:
    mode = settings.face_matcher_mode.lower()
    if mode == "disabled":
        return DisabledFaceMatcher()
    if mode == "histogram":
        return HistogramFaceMatcher(settings.face_match_threshold, reference_detector)
    if mode == "arcface":
        try:
            if not settings.face_match_model_path:
                raise FaceIdentityError("face embedding model path is not configured")
            return ArcFaceMatcher(
                settings.face_match_model_path,
                settings.face_match_threshold,
                reference_detector,
            )
        except FaceIdentityError:
            return HistogramFaceMatcher(0.92, reference_detector)
    raise FaceIdentityError(
        "unknown face matcher mode: "
        f"{settings.face_matcher_mode}; expected disabled, histogram, or arcface"
    )
