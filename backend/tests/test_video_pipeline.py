import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from backend.app.vision.detections import Detection, StaticDetector
from backend.app.vision.face_identity import HistogramFaceMatcher
from backend.app.vision.renderer import PrivacyRenderer
from backend.app.vision.tracker import DetectionTracker
from backend.app.vision.video_pipeline import BlurVideoPipeline, VideoPipelineCancelled


class SequenceDetector:
    def __init__(self, frames: list[list[Detection]]):
        self.frames = frames
        self.index = 0

    def detect(self, _frame):
        if self.index >= len(self.frames):
            return []
        detections = self.frames[self.index]
        self.index += 1
        return detections


class BlurVideoPipelineTests(unittest.TestCase):
    def test_processes_video_and_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "input.mp4"
            output_path = root / "output.mp4"
            self._write_video(input_path)

            pipeline = BlurVideoPipeline(
                detector=StaticDetector(
                    [
                        Detection(
                            kind="face",
                            x1=18,
                            y1=18,
                            x2=46,
                            y2=46,
                            confidence=1.0,
                        )
                    ]
                ),
                renderer=PrivacyRenderer(face_padding=0.0),
            )
            progress: list[tuple[int, str]] = []

            stats = pipeline.process_video(
                input_path,
                output_path,
                reference_image_path=None,
                mode="preserve",
                character_id=None,
                on_progress=lambda value, message: progress.append((value, message)),
                is_cancelled=lambda: False,
            )

            self.assertTrue(output_path.exists())
            self.assertEqual(stats["frames"], 4)
            self.assertEqual(stats["detections"], 4)
            self.assertEqual(progress[-1][0], 100)

    def test_cancel_raises_cancelled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "input.mp4"
            output_path = root / "output.mp4"
            self._write_video(input_path)
            pipeline = BlurVideoPipeline(
                detector=StaticDetector([]),
                renderer=PrivacyRenderer(),
            )

            with self.assertRaises(VideoPipelineCancelled):
                pipeline.process_video(
                    input_path,
                    output_path,
                    reference_image_path=None,
                    mode="preserve",
                    character_id=None,
                    on_progress=lambda _value, _message: None,
                    is_cancelled=lambda: True,
                )

    def test_preserves_matching_reference_face(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "input.mp4"
            output_path = root / "output.mp4"
            reference_path = root / "reference.jpg"
            self._write_video(input_path)
            reference = np.zeros((64, 64, 3), dtype=np.uint8)
            reference[:, :32] = (0, 0, 0)
            reference[:, 32:] = (255, 255, 255)
            cv2.imwrite(str(reference_path), reference)
            pipeline = BlurVideoPipeline(
                detector=StaticDetector(
                    [
                        Detection(
                            kind="face",
                            x1=0,
                            y1=0,
                            x2=64,
                            y2=64,
                            confidence=1.0,
                        )
                    ]
                ),
                renderer=PrivacyRenderer(face_padding=0.0),
                face_matcher=HistogramFaceMatcher(threshold=0.5),
            )

            stats = pipeline.process_video(
                input_path,
                output_path,
                reference_image_path=reference_path,
                mode="preserve",
                character_id=None,
                on_progress=lambda _value, _message: None,
                is_cancelled=lambda: False,
            )

            self.assertEqual(stats["preserved_faces"], 4)

    def test_preserves_multiple_reference_faces(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "input.mp4"
            output_path = root / "output.mp4"
            left_reference_path = root / "left.jpg"
            right_reference_path = root / "right.jpg"
            self._write_two_face_video(input_path)
            cv2.imwrite(str(left_reference_path), self._solid_image((0, 0, 255)))
            cv2.imwrite(str(right_reference_path), self._solid_image((0, 255, 0)))
            pipeline = BlurVideoPipeline(
                detector=StaticDetector(
                    [
                        Detection("face", 0, 0, 32, 64, 1.0),
                        Detection("face", 32, 0, 64, 64, 1.0),
                    ]
                ),
                renderer=PrivacyRenderer(face_padding=0.0),
                face_matcher=HistogramFaceMatcher(threshold=0.5),
            )

            stats = pipeline.process_video(
                input_path,
                output_path,
                reference_image_path=None,
                reference_image_paths=[left_reference_path, right_reference_path],
                mode="preserve",
                character_id=None,
                on_progress=lambda _value, _message: None,
                is_cancelled=lambda: False,
            )

            self.assertEqual(stats["reference_faces"], 2)
            self.assertEqual(stats["preserved_faces"], 8)

    def test_character_mode_overlays_matching_reference_face(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "input.mp4"
            output_path = root / "output.mp4"
            reference_path = root / "reference.jpg"
            self._write_video(input_path)
            reference = np.zeros((64, 64, 3), dtype=np.uint8)
            reference[:, :32] = (0, 0, 0)
            reference[:, 32:] = (255, 255, 255)
            cv2.imwrite(str(reference_path), reference)

            from backend.app.vision.character_overlay import CharacterAssetStore

            pipeline = BlurVideoPipeline(
                detector=StaticDetector(
                    [
                        Detection(
                            kind="face",
                            x1=0,
                            y1=0,
                            x2=64,
                            y2=64,
                            confidence=1.0,
                        )
                    ]
                ),
                renderer=PrivacyRenderer(face_padding=0.0),
                face_matcher=HistogramFaceMatcher(threshold=0.5),
                character_store=CharacterAssetStore(root / "assets"),
            )

            stats = pipeline.process_video(
                input_path,
                output_path,
                reference_image_path=reference_path,
                mode="character",
                character_id="missing_asset_uses_default",
                on_progress=lambda _value, _message: None,
                is_cancelled=lambda: False,
            )

            self.assertEqual(stats["overlaid_faces"], 4)
            self.assertTrue(output_path.exists())

    def test_tracker_retains_short_missing_detection_in_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "input.mp4"
            output_path = root / "output.mp4"
            self._write_video(input_path)
            pipeline = BlurVideoPipeline(
                detector=SequenceDetector(
                    [
                        [Detection("face", 18, 18, 46, 46, 1.0)],
                        [],
                        [],
                        [],
                    ]
                ),
                renderer=PrivacyRenderer(face_padding=0.0),
                tracker=DetectionTracker(iou_threshold=0.1, smoothing_alpha=0.5, max_missing=2),
            )

            stats = pipeline.process_video(
                input_path,
                output_path,
                reference_image_path=None,
                mode="preserve",
                character_id=None,
                on_progress=lambda _value, _message: None,
                is_cancelled=lambda: False,
            )

            self.assertEqual(stats["detections"], 1)
            self.assertEqual(stats["retained_missing_detections"], 2)

    def _write_video(self, path: Path) -> None:
        writer = cv2.VideoWriter(
            str(path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            5,
            (64, 64),
        )
        self.assertTrue(writer.isOpened())
        for _ in range(4):
            frame = np.zeros((64, 64, 3), dtype=np.uint8)
            frame[:, :32] = (0, 0, 0)
            frame[:, 32:] = (255, 255, 255)
            writer.write(frame)
        writer.release()

    def _write_two_face_video(self, path: Path) -> None:
        writer = cv2.VideoWriter(
            str(path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            5,
            (64, 64),
        )
        self.assertTrue(writer.isOpened())
        for _ in range(4):
            frame = np.zeros((64, 64, 3), dtype=np.uint8)
            frame[:, :32] = (0, 0, 255)
            frame[:, 32:] = (0, 255, 0)
            writer.write(frame)
        writer.release()

    @staticmethod
    def _solid_image(color: tuple[int, int, int]) -> np.ndarray:
        image = np.zeros((64, 64, 3), dtype=np.uint8)
        image[:, :] = color
        return image


if __name__ == "__main__":
    unittest.main()
