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


class _SequencedDetector:
    def __init__(self, frames: list[list[Detection]]):
        self.frames = frames
        self.index = 0

    def detect(self, frame: np.ndarray) -> list[Detection]:
        detections = self.frames[min(self.index, len(self.frames) - 1)]
        self.index += 1
        return detections


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

    def test_defaults_to_five_candidate_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video_path = root / "input.mp4"
            output_dir = root / "candidates"
            self._write_video(video_path, frame_count=1, size=(360, 96))
            detector = StaticDetector(
                [
                    Detection("face", x, 18, x + 44, 62, 0.95 - index * 0.01)
                    for index, x in enumerate([12, 68, 124, 180, 236, 292])
                ]
            )

            candidates = extract_video_face_candidates(
                video_path,
                detector,
                output_dir,
                max_frames=1,
            )

            self.assertEqual(len(candidates), 5)

    def test_prefers_frame_with_full_group_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video_path = root / "input.mp4"
            output_dir = root / "candidates"
            self._write_video(video_path, frame_count=2, size=(320, 96))
            detector = _SequencedDetector(
                [
                    [Detection("face", 24, 18, 68, 62, 0.91)],
                    [
                        Detection("face", x, 18, x + 44, 62, 0.94 - index * 0.01)
                        for index, x in enumerate([16, 76, 136, 196, 256])
                    ],
                ]
            )

            candidates = extract_video_face_candidates(
                video_path,
                detector,
                output_dir,
                max_frames=2,
                max_candidates=5,
            )

            self.assertEqual(len(candidates), 5)
            self.assertEqual({candidate.frame_index for candidate in candidates}, {1})

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

    def _write_video(
        self,
        path: Path,
        frame_count: int = 4,
        size: tuple[int, int] = (128, 64),
    ) -> None:
        width, height = size
        writer = cv2.VideoWriter(
            str(path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            5,
            (width, height),
        )
        self.assertTrue(writer.isOpened())
        for _ in range(frame_count):
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            for index, x in enumerate([8, 12, 68, 72, 124, 180, 196, 236, 256, 292]):
                if x + 44 >= width or 62 >= height:
                    continue
                frame[18:62, x : x + 44] = (
                    255 - index * 12,
                    255 - index * 10,
                    255 - index * 8,
                )
                frame[18:62:4, x : x + 44] = (0, 0, 0)
                frame[18:62, x : x + 44 : 4] = (255, 255, 255)
            writer.write(frame)
        writer.release()


if __name__ == "__main__":
    unittest.main()
