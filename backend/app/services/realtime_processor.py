from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import cv2
import numpy as np

from backend.app.vision.character_overlay import CharacterAssetStore
from backend.app.vision.detections import RegionDetector
from backend.app.vision.face_identity import FaceIdentityMatcher, PreparedFaceMatcher
from backend.app.vision.renderer import OverlayInstruction, PrivacyRenderer
from backend.app.vision.tracker import DetectionTracker


class RealtimeFrameError(RuntimeError):
    pass


@dataclass
class RealtimeRuntime:
    mode: str
    character_id: str | None
    prepared_matcher: PreparedFaceMatcher | None
    character_image: np.ndarray | None
    tracker: DetectionTracker | None


class RealtimeFrameProcessor:
    def __init__(
        self,
        detector: RegionDetector,
        renderer: PrivacyRenderer,
        face_matcher: FaceIdentityMatcher | None,
        character_store: CharacterAssetStore | None,
        tracker_factory: Callable[[], DetectionTracker | None],
        output_format: str = ".jpg",
        max_pixels: int | None = None,
    ):
        self.detector = detector
        self.renderer = renderer
        self.face_matcher = face_matcher
        self.character_store = character_store
        self.tracker_factory = tracker_factory
        self.output_format = output_format
        self.max_pixels = max_pixels

    def create_runtime(
        self,
        reference_image_path: Path,
        mode: str,
        character_id: str | None,
    ) -> RealtimeRuntime:
        prepared_matcher = (
            self.face_matcher.prepare(reference_image_path) if self.face_matcher else None
        )
        character_image = None
        if mode == "character" and self.character_store:
            character_image = self.character_store.load(character_id)
        return RealtimeRuntime(
            mode=mode,
            character_id=character_id,
            prepared_matcher=prepared_matcher,
            character_image=character_image,
            tracker=self.tracker_factory(),
        )

    def process_frame(self, data: bytes, runtime: RealtimeRuntime) -> bytes:
        frame = self._decode(data)
        raw_detections = self.detector.detect(frame)
        detections = runtime.tracker.update(raw_detections) if runtime.tracker else raw_detections
        render_detections = []
        overlays: list[OverlayInstruction] = []

        for detection in detections:
            if detection.kind == "face" and runtime.prepared_matcher and detection.observed:
                is_reference = runtime.prepared_matcher.is_match(frame, detection)
                if runtime.mode == "preserve" and is_reference:
                    continue
                if (
                    runtime.mode == "character"
                    and is_reference
                    and runtime.character_image is not None
                ):
                    overlays.append(
                        OverlayInstruction(
                            detection=detection,
                            image=runtime.character_image,
                        )
                    )
                    continue
            render_detections.append(detection)

        rendered = self.renderer.render(frame, render_detections, overlays)
        return self._encode(rendered)

    def _decode(self, data: bytes) -> np.ndarray:
        array = np.frombuffer(data, dtype=np.uint8)
        frame = cv2.imdecode(array, cv2.IMREAD_COLOR)
        if frame is None or frame.size == 0:
            raise RealtimeFrameError("cannot decode realtime frame")
        if self.max_pixels is not None:
            height, width = frame.shape[:2]
            if height * width > self.max_pixels:
                raise RealtimeFrameError(
                    f"realtime frame is too large: {width}x{height} > {self.max_pixels} pixels"
                )
        return frame

    def _encode(self, frame: np.ndarray) -> bytes:
        ok, encoded = cv2.imencode(self.output_format, frame)
        if not ok:
            raise RealtimeFrameError("cannot encode realtime frame")
        return encoded.tobytes()
