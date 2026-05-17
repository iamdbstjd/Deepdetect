from __future__ import annotations

from pathlib import Path
import threading

import cv2
import numpy as np

from backend.app.core.config import Settings
from backend.app.vision.detections import Detection, NoopDetector, RegionDetector


class DetectorConfigurationError(RuntimeError):
    pass


class YoloRegionDetector:
    def __init__(
        self,
        face_model_path: Path | None,
        plate_model_path: Path | None,
        confidence: float = 0.35,
    ):
        try:
            from ultralytics import YOLO
        except ImportError as exc:  # pragma: no cover - dependency checked at runtime.
            raise DetectorConfigurationError("ultralytics is not installed") from exc

        self.confidence = confidence
        self._lock = threading.RLock()
        self._models: list[tuple[str, object]] = []
        if face_model_path and face_model_path.exists():
            self._models.append(("face", YOLO(str(face_model_path))))
        if plate_model_path and plate_model_path.exists():
            self._models.append(("plate", YOLO(str(plate_model_path))))
        if not self._models:
            raise DetectorConfigurationError("no YOLO model files found")

    def detect(self, frame: np.ndarray) -> list[Detection]:
        detections: list[Detection] = []
        for kind, model in self._models:
            with self._lock:
                results = model.predict(frame, conf=self.confidence, verbose=False)
            for result in results:
                boxes = getattr(result, "boxes", None)
                if boxes is None:
                    continue
                for box in boxes:
                    confidence = float(box.conf[0]) if box.conf is not None else 0.0
                    x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                    detections.append(
                        Detection(
                            kind=kind,
                            x1=x1,
                            y1=y1,
                            x2=x2,
                            y2=y2,
                            confidence=confidence,
                            label=kind,
                        )
                    )
        return detections


class HaarFaceFallbackDetector:
    """Development-only fallback used when YOLO weights are not present.

    This is not the final detector for the project. It keeps the Phase 2 video
    pipeline testable until YOLO face/plate weights are placed under `models/`.
    """

    def __init__(self):
        cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        self.classifier = cv2.CascadeClassifier(str(cascade_path))
        if self.classifier.empty():
            raise DetectorConfigurationError("OpenCV Haar face cascade is unavailable")

    def detect(self, frame: np.ndarray) -> list[Detection]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.classifier.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(32, 32),
        )
        return [
            Detection(
                kind="face",
                x1=int(x),
                y1=int(y),
                x2=int(x + w),
                y2=int(y + h),
                confidence=1.0,
                label="haar_face_fallback",
            )
            for x, y, w, h in faces
        ]


def build_detector(settings: Settings) -> RegionDetector:
    mode = settings.detector_mode.lower()
    if mode == "noop":
        return NoopDetector()
    if mode == "haar":
        return HaarFaceFallbackDetector()
    if mode == "yolo":
        return YoloRegionDetector(
            settings.yolo_face_model_path,
            settings.yolo_plate_model_path,
            settings.detector_confidence,
        )
    if mode == "auto":
        try:
            return YoloRegionDetector(
                settings.yolo_face_model_path,
                settings.yolo_plate_model_path,
                settings.detector_confidence,
            )
        except DetectorConfigurationError:
            return HaarFaceFallbackDetector()
    raise DetectorConfigurationError(
        f"unknown detector mode: {settings.detector_mode}; expected auto, yolo, haar, or noop"
    )
