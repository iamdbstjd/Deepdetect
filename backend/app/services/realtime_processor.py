from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import threading
import time
from typing import Callable
import uuid

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
class RealtimePromptCandidate:
    candidate_id: str
    image_bytes: bytes
    track_id: int


@dataclass
class RealtimeFrameResult:
    image: bytes
    candidates: list[RealtimePromptCandidate]


@dataclass
class _UnknownFaceTrack:
    first_seen: float
    last_seen: float
    prompted: bool = False
    candidate_id: str | None = None


@dataclass
class RealtimeRuntime:
    mode: str
    character_id: str | None
    prepared_matchers: list[PreparedFaceMatcher]
    character_image: np.ndarray | None
    tracker: DetectionTracker | None
    unknown_prompt_seconds: float = 10.0
    reference_track_ids: set[int] = field(default_factory=set)
    unknown_tracks: dict[int, _UnknownFaceTrack] = field(default_factory=dict)
    pending_faces: dict[str, bytes] = field(default_factory=dict)
    lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    @property
    def prepared_matcher(self) -> PreparedFaceMatcher | None:
        return self.prepared_matchers[0] if self.prepared_matchers else None


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
        reference_image_path: Path | None,
        mode: str,
        character_id: str | None,
        reference_image_paths: list[Path] | None = None,
    ) -> RealtimeRuntime:
        prepared_matchers = self._prepare_matchers(
            reference_image_path,
            reference_image_paths,
        )
        character_image = None
        if mode == "character" and self.character_store:
            character_image = self.character_store.load(character_id)
        return RealtimeRuntime(
            mode=mode,
            character_id=character_id,
            prepared_matchers=prepared_matchers,
            character_image=character_image,
            tracker=self.tracker_factory(),
        )

    def process_frame(self, data: bytes, runtime: RealtimeRuntime) -> bytes:
        return self.process_frame_with_metadata(data, runtime).image

    def process_frame_with_metadata(
        self,
        data: bytes,
        runtime: RealtimeRuntime,
        now: float | None = None,
    ) -> RealtimeFrameResult:
        now = time.monotonic() if now is None else now
        frame = self._decode(data)
        raw_detections = self.detector.detect(frame)
        detections = runtime.tracker.update(raw_detections) if runtime.tracker else raw_detections
        render_detections = []
        overlays: list[OverlayInstruction] = []
        prompt_candidates: list[RealtimePromptCandidate] = []

        with runtime.lock:
            visible_unknown_track_ids: set[int] = set()
            for detection in detections:
                if detection.kind == "face":
                    is_reference = self._is_reference(frame, detection, runtime)
                    if is_reference:
                        if detection.track_id is not None:
                            runtime.unknown_tracks.pop(detection.track_id, None)
                        if runtime.mode == "preserve":
                            continue
                        if (
                            runtime.mode == "character"
                            and runtime.character_image is not None
                            and detection.observed
                        ):
                            overlays.append(
                                OverlayInstruction(
                                    detection=detection,
                                    image=runtime.character_image,
                                )
                            )
                            continue
                        if runtime.mode == "character":
                            continue
                    elif detection.observed and detection.track_id is not None:
                        visible_unknown_track_ids.add(detection.track_id)
                        candidate = self._maybe_prompt_candidate(
                            frame,
                            detection,
                            runtime,
                            now,
                        )
                        if candidate:
                            prompt_candidates.append(candidate)
                render_detections.append(detection)

            self._drop_stale_unknown_tracks(runtime, visible_unknown_track_ids, now)

        rendered = self.renderer.render(frame, render_detections, overlays)
        return RealtimeFrameResult(
            image=self._encode(rendered),
            candidates=prompt_candidates,
        )

    def allow_pending_face(
        self,
        runtime: RealtimeRuntime,
        candidate_id: str,
        reference_image_path: Path,
    ) -> bool:
        if not self.face_matcher:
            return False
        with runtime.lock:
            image_bytes = runtime.pending_faces.pop(candidate_id, None)
            if image_bytes is None:
                return False
            reference_image_path.parent.mkdir(parents=True, exist_ok=True)
            reference_image_path.write_bytes(image_bytes)
            runtime.prepared_matchers.append(self.face_matcher.prepare(reference_image_path))
            for track_id, track in runtime.unknown_tracks.items():
                if track.candidate_id == candidate_id:
                    track.prompted = True
                    runtime.reference_track_ids.add(track_id)
            return True

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

    def _prepare_matchers(
        self,
        reference_image_path: Path | None,
        reference_image_paths: list[Path] | None,
    ) -> list[PreparedFaceMatcher]:
        if not self.face_matcher:
            return []
        unique_paths: list[Path] = []
        seen: set[str] = set()
        for path in [reference_image_path, *(reference_image_paths or [])]:
            if not path:
                continue
            normalized = str(path)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            unique_paths.append(path)
        return [self.face_matcher.prepare(path) for path in unique_paths]

    @staticmethod
    def _is_reference(
        frame: np.ndarray,
        detection,
        runtime: RealtimeRuntime,
    ) -> bool:
        track_id = detection.track_id
        if track_id is not None and track_id in runtime.reference_track_ids:
            return True
        if not detection.observed:
            return False
        is_reference = any(
            matcher.is_match(frame, detection)
            for matcher in runtime.prepared_matchers
        )
        if is_reference and track_id is not None:
            runtime.reference_track_ids.add(track_id)
        return is_reference

    def _maybe_prompt_candidate(
        self,
        frame: np.ndarray,
        detection,
        runtime: RealtimeRuntime,
        now: float,
    ) -> RealtimePromptCandidate | None:
        track_id = detection.track_id
        if track_id is None:
            return None
        track = runtime.unknown_tracks.get(track_id)
        if track is None:
            runtime.unknown_tracks[track_id] = _UnknownFaceTrack(
                first_seen=now,
                last_seen=now,
            )
            return None
        track.last_seen = now
        if track.prompted or now - track.first_seen < runtime.unknown_prompt_seconds:
            return None

        crop = self._crop_detection(frame, detection)
        if crop.size == 0:
            return None
        image_bytes = self._encode(crop)
        candidate_id = f"rt_{uuid.uuid4().hex[:12]}"
        runtime.pending_faces[candidate_id] = image_bytes
        track.prompted = True
        track.candidate_id = candidate_id
        return RealtimePromptCandidate(
            candidate_id=candidate_id,
            image_bytes=image_bytes,
            track_id=track_id,
        )

    @staticmethod
    def _drop_stale_unknown_tracks(
        runtime: RealtimeRuntime,
        visible_unknown_track_ids: set[int],
        now: float,
    ) -> None:
        stale_after = max(2.0, runtime.unknown_prompt_seconds * 1.5)
        for track_id, track in list(runtime.unknown_tracks.items()):
            if track_id in visible_unknown_track_ids:
                continue
            if now - track.last_seen >= stale_after:
                del runtime.unknown_tracks[track_id]

    @staticmethod
    def _crop_detection(frame: np.ndarray, detection) -> np.ndarray:
        height, width = frame.shape[:2]
        box = detection.clipped(width, height, padding_ratio=0.18)
        if not box.is_valid:
            return np.empty((0, 0, 3), dtype=frame.dtype)
        return frame[box.y1 : box.y2, box.x1 : box.x2]
