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
from backend.app.services.realtime_processor import RealtimeFrameProcessor


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

    @staticmethod
    def _frame() -> np.ndarray:
        frame = np.zeros((64, 64, 3), dtype=np.uint8)
        frame[:, :32] = (0, 0, 0)
        frame[:, 32:] = (255, 255, 255)
        return frame


if __name__ == "__main__":
    unittest.main()

