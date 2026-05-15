import unittest
from pathlib import Path

import cv2
import numpy as np

from backend.app.vision.detections import Detection
from backend.app.vision.face_identity import ArcFaceMatcher, HistogramFaceMatcher


class FaceIdentityTests(unittest.TestCase):
    def test_histogram_matcher_matches_same_region(self) -> None:
        image = self._face_like_image()
        path = self._write_image("hist_reference.jpg", image)
        matcher = HistogramFaceMatcher(threshold=0.5).prepare(path)

        self.assertTrue(matcher.is_match(image, Detection("face", 0, 0, 112, 112, 1.0)))

    def test_arcface_matcher_loads_and_scores_same_region(self) -> None:
        model_path = Path("models/face/w600k_r50.onnx")
        self.assertTrue(model_path.exists())
        image = self._face_like_image()
        path = self._write_image("arc_reference.jpg", image)
        matcher = ArcFaceMatcher(model_path, threshold=0.2).prepare(path)

        score = matcher.match_score(image, Detection("face", 0, 0, 112, 112, 1.0))

        self.assertGreaterEqual(score, 0.99)

    @staticmethod
    def _face_like_image() -> np.ndarray:
        image = np.full((112, 112, 3), 180, dtype=np.uint8)
        cv2.circle(image, (38, 44), 8, (40, 40, 40), -1)
        cv2.circle(image, (74, 44), 8, (40, 40, 40), -1)
        cv2.ellipse(image, (56, 72), (24, 12), 0, 0, 180, (40, 40, 40), 4)
        return image

    @staticmethod
    def _write_image(name: str, image: np.ndarray) -> Path:
        path = Path("/tmp") / name
        cv2.imwrite(str(path), image)
        return path


if __name__ == "__main__":
    unittest.main()

