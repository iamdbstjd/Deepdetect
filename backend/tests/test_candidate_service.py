import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from backend.app.services.candidate_service import extract_video_face_candidates
from backend.app.vision.detections import Detection, StaticDetector


class CandidateServiceTests(unittest.TestCase):
    def test_extracts_face_candidates_from_video(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video_path = root / "input.mp4"
            output_dir = root / "candidates"
            self._write_video(video_path)
            detector = StaticDetector([Detection("face", 12, 12, 52, 52, 0.91)])

            candidates = extract_video_face_candidates(
                video_path,
                detector,
                output_dir,
                max_frames=4,
                max_candidates=3,
            )

            self.assertEqual(len(candidates), 1)
            self.assertEqual(candidates[0].candidate_id, "face_0001")
            self.assertTrue(candidates[0].image_path.exists())
            self.assertGreater(candidates[0].image_path.stat().st_size, 0)

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
            frame[12:52, 12:52] = (255, 255, 255)
            writer.write(frame)
        writer.release()


if __name__ == "__main__":
    unittest.main()
