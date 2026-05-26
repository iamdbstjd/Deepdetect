from __future__ import annotations

from pathlib import Path
from typing import Callable

import cv2

from backend.app.vision.character_overlay import CharacterAssetStore
from backend.app.vision.detections import RegionDetector
from backend.app.vision.face_identity import FaceIdentityMatcher, PreparedFaceMatcher
from backend.app.vision.renderer import OverlayInstruction, PrivacyRenderer
from backend.app.vision.tracker import DetectionTracker


ProgressCallback = Callable[[int, str], None]
CancelledCallback = Callable[[], bool]


class VideoPipelineError(RuntimeError):
    pass


class VideoPipelineCancelled(RuntimeError):
    pass


class BlurVideoPipeline:
    def __init__(
        self,
        detector: RegionDetector,
        renderer: PrivacyRenderer,
        face_matcher: FaceIdentityMatcher | None = None,
        character_store: CharacterAssetStore | None = None,
        tracker: DetectionTracker | None = None,
    ):
        self.detector = detector
        self.renderer = renderer
        self.face_matcher = face_matcher
        self.character_store = character_store
        self.tracker = tracker

    def process_video(
        self,
        input_path: Path,
        output_path: Path,
        reference_image_path: Path | None,
        mode: str,
        character_id: str | None,
        on_progress: ProgressCallback,
        is_cancelled: CancelledCallback,
        reference_image_paths: list[Path] | None = None,
    ) -> dict[str, int]:
        capture = cv2.VideoCapture(str(input_path))
        if not capture.isOpened():
            raise VideoPipelineError(f"cannot open video: {input_path}")

        fps = capture.get(cv2.CAP_PROP_FPS) or 30
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if width <= 0 or height <= 0:
            capture.release()
            raise VideoPipelineError("video has invalid dimensions")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        writer = cv2.VideoWriter(
            str(output_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (width, height),
        )
        if not writer.isOpened():
            capture.release()
            raise VideoPipelineError(f"cannot create output video: {output_path}")

        processed = 0
        total_detections = 0
        tracked_detections = 0
        preserved_faces = 0
        overlaid_faces = 0
        retained_missing = 0
        if self.tracker:
            self.tracker.reset()
        prepared_matchers = self._prepare_matchers(
            reference_image_path,
            reference_image_paths,
        )
        character_image = None
        if mode == "character" and self.character_store:
            character_image = self.character_store.load(character_id)
        try:
            while True:
                if is_cancelled():
                    raise VideoPipelineCancelled("video processing was cancelled")
                ok, frame = capture.read()
                if not ok:
                    break
                raw_detections = self.detector.detect(frame)
                detections = self.tracker.update(raw_detections) if self.tracker else raw_detections
                render_detections = []
                overlays: list[OverlayInstruction] = []
                for detection in detections:
                    if detection.kind == "face" and prepared_matchers and detection.observed:
                        is_reference = any(
                            matcher.is_match(frame, detection)
                            for matcher in prepared_matchers
                        )
                        if mode == "preserve" and is_reference:
                            preserved_faces += 1
                            continue
                        if mode == "character" and is_reference and character_image is not None:
                            overlaid_faces += 1
                            overlays.append(
                                OverlayInstruction(detection=detection, image=character_image)
                            )
                            continue
                    render_detections.append(detection)
                total_detections += len(raw_detections)
                tracked_detections += len(detections)
                retained_missing += sum(1 for detection in detections if not detection.observed)
                writer.write(self.renderer.render(frame, render_detections, overlays))
                processed += 1
                if processed == 1 or processed % 10 == 0:
                    progress = self._progress(processed, total_frames)
                    on_progress(progress, f"Processed frame {processed} / {total_frames or '?'}")
        finally:
            capture.release()
            writer.release()

        if processed == 0:
            raise VideoPipelineError("no frames were processed")

        on_progress(100, "Blur video result ready")
        return {
            "frames": processed,
            "detections": total_detections,
            "tracked_detections": tracked_detections,
            "retained_missing_detections": retained_missing,
            "preserved_faces": preserved_faces,
            "overlaid_faces": overlaid_faces,
            "reference_faces": len(prepared_matchers),
            "width": width,
            "height": height,
        }

    @staticmethod
    def _progress(processed: int, total_frames: int) -> int:
        if total_frames <= 0:
            return min(95, 5 + processed)
        return min(99, max(1, int((processed / total_frames) * 100)))

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
