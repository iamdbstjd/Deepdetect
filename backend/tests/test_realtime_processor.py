import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from backend.app.vision.character_overlay import CharacterAssetStore
from backend.app.vision.detections import Detection, StaticDetector
from backend.app.vision.face_identity import HistogramFaceMatcher
from backend.app.vision.renderer import PrivacyRenderer
from backend.app.vision.tracker import DetectionTracker
from backend.app.services.realtime_processor import RealtimeFrameError, RealtimeFrameProcessor


class SequencePreparedMatcher:
    def __init__(self, responses: list[bool]):
        self.responses = responses
        self.index = 0

    def match_score(self, _frame: np.ndarray, _detection: Detection) -> float:
        return 1.0 if self.is_match(_frame, _detection) else 0.0

    def is_match(self, _frame: np.ndarray, _detection: Detection) -> bool:
        if self.index >= len(self.responses):
            return False
        response = self.responses[self.index]
        self.index += 1
        return response


class SequenceFaceMatcher:
    def __init__(self, responses: list[bool]):
        self.responses = responses

    def prepare(self, _reference_image_path: Path) -> SequencePreparedMatcher:
        return SequencePreparedMatcher(self.responses)


class RealtimeFrameProcessorTests(unittest.TestCase):
    def test_processes_frame(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reference_path = root / "reference.jpg"
            frame = self._frame()
            cv2.imwrite(str(reference_path), frame)
            ok, encoded = cv2.imencode(".jpg", frame)
            self.assertTrue(ok)
            processor = RealtimeFrameProcessor(
                detector=StaticDetector([Detection("face", 0, 0, 64, 64, 1.0)]),
                renderer=PrivacyRenderer(face_padding=0.0),
                face_matcher=HistogramFaceMatcher(threshold=0.5),
                character_store=CharacterAssetStore(root / "assets"),
                tracker_factory=lambda: DetectionTracker(max_missing=1),
            )
            runtime = processor.create_runtime(reference_path, "character", None)

            result = processor.process_frame(encoded.tobytes(), runtime)
            decoded = cv2.imdecode(np.frombuffer(result, dtype=np.uint8), cv2.IMREAD_COLOR)

            self.assertIsNotNone(decoded)
            self.assertEqual(decoded.shape[:2], (64, 64))

    def test_rejects_decoded_frame_above_pixel_limit(self) -> None:
        frame = self._frame()
        ok, encoded = cv2.imencode(".jpg", frame)
        self.assertTrue(ok)
        processor = RealtimeFrameProcessor(
            detector=StaticDetector([]),
            renderer=PrivacyRenderer(),
            face_matcher=None,
            character_store=None,
            tracker_factory=lambda: None,
            max_pixels=32 * 32,
        )
        runtime = processor.create_runtime(Path("/tmp/reference_unused.jpg"), "preserve", None)

        with self.assertRaises(RealtimeFrameError):
            processor.process_frame(encoded.tobytes(), runtime)

    def test_prompts_for_unknown_face_after_threshold(self) -> None:
        frame = self._frame()
        ok, encoded = cv2.imencode(".jpg", frame)
        self.assertTrue(ok)
        processor = RealtimeFrameProcessor(
            detector=StaticDetector([Detection("face", 0, 0, 64, 64, 1.0)]),
            renderer=PrivacyRenderer(face_padding=0.0),
            face_matcher=None,
            character_store=None,
            tracker_factory=lambda: DetectionTracker(max_missing=1),
        )
        runtime = processor.create_runtime(None, "preserve", None)

        first = processor.process_frame_with_metadata(encoded.tobytes(), runtime, now=0.0)
        second = processor.process_frame_with_metadata(encoded.tobytes(), runtime, now=10.5)

        self.assertEqual(first.candidates, [])
        self.assertEqual(len(second.candidates), 1)
        self.assertTrue(second.candidates[0].candidate_id.startswith("rt_"))

    def test_allow_pending_face_adds_reference_matcher(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frame = self._frame()
            ok, encoded = cv2.imencode(".jpg", frame)
            self.assertTrue(ok)
            processor = RealtimeFrameProcessor(
                detector=StaticDetector([Detection("face", 0, 0, 64, 64, 1.0)]),
                renderer=PrivacyRenderer(face_padding=0.0),
                face_matcher=HistogramFaceMatcher(threshold=0.5),
                character_store=None,
                tracker_factory=lambda: DetectionTracker(max_missing=1),
            )
            runtime = processor.create_runtime(None, "preserve", None)

            processor.process_frame_with_metadata(encoded.tobytes(), runtime, now=0.0)
            result = processor.process_frame_with_metadata(encoded.tobytes(), runtime, now=10.5)
            accepted = processor.allow_pending_face(
                runtime,
                result.candidates[0].candidate_id,
                root / "allowed.jpg",
            )

            self.assertTrue(accepted)
            self.assertEqual(len(runtime.prepared_matchers), 1)

    def test_keeps_reference_track_when_later_angle_does_not_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reference_path = root / "reference.jpg"
            frame = self._frame()
            cv2.imwrite(str(reference_path), frame)
            ok, encoded = cv2.imencode(".jpg", frame)
            self.assertTrue(ok)
            processor = RealtimeFrameProcessor(
                detector=StaticDetector([Detection("face", 0, 0, 64, 64, 1.0)]),
                renderer=PrivacyRenderer(face_padding=0.0),
                face_matcher=SequenceFaceMatcher([True, False]),
                character_store=None,
                tracker_factory=lambda: DetectionTracker(iou_threshold=0.1, max_missing=1),
            )
            runtime = processor.create_runtime(reference_path, "preserve", None)

            first = processor.process_frame_with_metadata(encoded.tobytes(), runtime, now=0.0)
            second = processor.process_frame_with_metadata(encoded.tobytes(), runtime, now=20.0)

            self.assertEqual(first.candidates, [])
            self.assertEqual(second.candidates, [])
            self.assertEqual(runtime.reference_track_ids, {1})

    @staticmethod
    def _frame() -> np.ndarray:
        frame = np.zeros((64, 64, 3), dtype=np.uint8)
        frame[:, :32] = (0, 0, 0)
        frame[:, 32:] = (255, 255, 255)
        return frame


if __name__ == "__main__":
    unittest.main()
