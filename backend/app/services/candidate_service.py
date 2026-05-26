from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from backend.app.vision.detections import Detection, RegionDetector


@dataclass(frozen=True)
class VideoFaceCandidate:
    candidate_id: str
    image_path: Path
    frame_index: int
    confidence: float


def extract_video_face_candidates(
    video_path: Path,
    detector: RegionDetector,
    output_dir: Path,
    max_frames: int = 90,
    max_candidates: int = 18,
    duplicate_threshold: float = 0.94,
) -> list[VideoFaceCandidate]:
    output_dir.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise ValueError(f"cannot open video: {video_path}")

    candidates: list[VideoFaceCandidate] = []
    histograms: list[np.ndarray] = []
    try:
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        positions = _sample_positions(total_frames, max_frames)
        for frame_index in positions:
            if len(candidates) >= max_candidates:
                break
            if total_frames > 0:
                capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = capture.read()
            if not ok:
                break
            for detection in _face_detections(frame, detector.detect(frame)):
                if len(candidates) >= max_candidates:
                    break
                crop = _crop_face(frame, detection)
                if crop.size == 0:
                    continue
                histogram = _candidate_histogram(crop)
                if _is_duplicate(histogram, histograms, duplicate_threshold):
                    continue
                candidate_id = f"face_{len(candidates) + 1:04d}"
                image_path = output_dir / f"{candidate_id}.jpg"
                cv2.imwrite(str(image_path), crop)
                histograms.append(histogram)
                candidates.append(
                    VideoFaceCandidate(
                        candidate_id=candidate_id,
                        image_path=image_path,
                        frame_index=frame_index,
                        confidence=detection.confidence,
                    )
                )
    finally:
        capture.release()
    return candidates


def _sample_positions(total_frames: int, max_frames: int) -> list[int]:
    if max_frames <= 0:
        return []
    if total_frames <= 0:
        return list(range(max_frames))
    sample_count = min(total_frames, max_frames)
    if sample_count <= 1:
        return [0]
    return sorted(
        {
            round(index * (total_frames - 1) / (sample_count - 1))
            for index in range(sample_count)
        }
    )


def _face_detections(frame: np.ndarray, detections: list[Detection]) -> list[Detection]:
    height, width = frame.shape[:2]
    min_side = max(18, int(min(width, height) * 0.04))
    faces = [
        detection.clipped(width, height, padding_ratio=0.0)
        for detection in detections
        if detection.kind == "face" and detection.observed
    ]
    valid = [
        detection
        for detection in faces
        if detection.is_valid
        and detection.x2 - detection.x1 >= min_side
        and detection.y2 - detection.y1 >= min_side
    ]
    return sorted(valid, key=lambda item: item.confidence, reverse=True)


def _crop_face(frame: np.ndarray, detection: Detection) -> np.ndarray:
    height, width = frame.shape[:2]
    box = detection.clipped(width, height, padding_ratio=0.18)
    if not box.is_valid:
        return np.empty((0, 0, 3), dtype=frame.dtype)
    return frame[box.y1 : box.y2, box.x1 : box.x2]


def _candidate_histogram(image: np.ndarray) -> np.ndarray:
    resized = cv2.resize(image, (96, 96), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
    histogram = cv2.calcHist([hsv], [0, 1], None, [32, 32], [0, 180, 0, 256])
    cv2.normalize(histogram, histogram, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
    return histogram


def _is_duplicate(
    histogram: np.ndarray,
    existing: list[np.ndarray],
    threshold: float,
) -> bool:
    return any(
        cv2.compareHist(histogram, current, cv2.HISTCMP_CORREL) >= threshold
        for current in existing
    )
