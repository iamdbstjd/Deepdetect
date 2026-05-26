import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from backend.app.services.candidate_service import extract_video_face_candidates
from backend.app.vision.detections import Detection, StaticDetector


class _AlwaysMatchPreparedMatcher:
    def match_score(self, frame: np.ndarray, detection: Detection) -> float:
        return 1.0

    def is_match(self, frame: np.ndarray, detection: Detection) -> bool:
        return True


class _AlwaysMatchFaceMatcher:
    def prepare(self, reference_image_path: Path) -> _AlwaysMatchPreparedMatcher:
        return _AlwaysMatchPreparedMatcher()


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

    def test_identity_matcher_collapses_duplicate_people(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video_path = root / "input.mp4"
            output_dir = root / "candidates"
            self._write_video(video_path, frame_count=1)
            detector = StaticDetector(
                [
                    Detection("face", 8, 8, 52, 52, 0.91),
                    Detection("face", 72, 8, 116, 52, 0.88),
                ]
            )

            candidates = extract_video_face_candidates(
                video_path,
                detector,
                output_dir,
                max_frames=1,
                duplicate_threshold=1.01,
                face_matcher=_AlwaysMatchFaceMatcher(),
            )

            self.assertEqual(len(candidates), 1)

    def test_rejects_partial_edge_faces(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video_path = root / "input.mp4"
            output_dir = root / "candidates"
            self._write_video(video_path, frame_count=1)
            detector = StaticDetector([Detection("face", 0, 8, 44, 52, 0.91)])

            candidates = extract_video_face_candidates(
                video_path,
                detector,
                output_dir,
                max_frames=1,
            )

            self.assertEqual(candidates, [])

    def _write_video(self, path: Path, frame_count: int = 4) -> None:
        writer = cv2.VideoWriter(
            str(path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            5,
            (128, 64),
        )
        self.assertTrue(writer.isOpened())
        for _ in range(frame_count):
            frame = np.zeros((64, 128, 3), dtype=np.uint8)
            frame[8:52, 8:52] = (255, 255, 255)
            frame[8:52, 72:116] = (180, 180, 180)
            writer.write(frame)
        writer.release()


if __name__ == "__main__":
    unittest.main()
