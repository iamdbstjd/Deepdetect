from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from backend.app.vision.detections import Detection, RegionDetector
from backend.app.vision.face_identity import (
    FaceIdentityError,
    FaceIdentityMatcher,
    PreparedFaceMatcher,
)
from backend.app.vision.tracker import DetectionTracker


@dataclass(frozen=True)
class VideoFaceCandidate:
    candidate_id: str
    image_path: Path
    frame_index: int
    confidence: float


@dataclass(frozen=True)
class _FaceObservation:
    frame_index: int
    detection: Detection
    crop: np.ndarray
    histogram: np.ndarray
    sharpness: float
    quality: float


@dataclass
class _Representative:
    histogram: np.ndarray
    matcher: PreparedFaceMatcher | None
    track_ids: set[int]


def extract_video_face_candidates(
    video_path: Path,
    detector: RegionDetector,
    output_dir: Path,
    max_frames: int = 90,
    max_candidates: int = 5,
    duplicate_threshold: float = 0.86,
    duplicate_identity_threshold: float = 0.30,
    face_matcher: FaceIdentityMatcher | None = None,
) -> list[VideoFaceCandidate]:
    output_dir.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise ValueError(f"cannot open video: {video_path}")

    candidates: list[VideoFaceCandidate] = []
    observations: list[_FaceObservation] = []
    group_frames: list[list[_FaceObservation]] = []
    tracker = DetectionTracker(iou_threshold=0.25, smoothing_alpha=0.55, max_missing=8)
    try:
        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        positions = _sample_positions(total_frames, max_frames)
        for frame_index in positions:
            if total_frames > 0:
                capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = capture.read()
            if not ok:
                break
            tracked_detections = tracker.update(_face_detections(frame, detector.detect(frame)))
            frame_observations: list[_FaceObservation] = []
            for detection in _face_detections(frame, tracked_detections):
                crop = _crop_face(frame, detection)
                sharpness = _sharpness(crop)
                if crop.size == 0 or _is_low_quality_candidate(
                    frame,
                    detection,
                    crop,
                    sharpness,
                ):
                    continue
                observation = _FaceObservation(
                    frame_index=frame_index,
                    detection=detection,
                    crop=crop,
                    histogram=_candidate_histogram(crop),
                    sharpness=sharpness,
                    quality=_candidate_quality(frame, detection, sharpness),
                )
                observations.append(observation)
                frame_observations.append(observation)
            if len(frame_observations) >= max_candidates:
                group_frames.append(frame_observations)
    finally:
        capture.release()

    group_observations = _select_group_frame_observations(group_frames, max_candidates)
    if group_observations:
        return _write_candidates(group_observations, output_dir, face_matcher)

    representatives: list[_Representative] = []
    usable_observations = _keep_clear_observations(observations)
    for observation in sorted(usable_observations, key=lambda item: item.quality, reverse=True):
        if len(candidates) >= max_candidates:
            break
        if _is_duplicate_observation(
            observation,
            representatives,
            duplicate_threshold,
            duplicate_identity_threshold,
        ):
            continue
        candidates.extend(
            _write_candidates(
                [observation],
                output_dir,
                face_matcher,
                start_index=len(candidates),
                representatives=representatives,
            )
        )
    return candidates


def _write_candidates(
    observations: list[_FaceObservation],
    output_dir: Path,
    face_matcher: FaceIdentityMatcher | None,
    start_index: int = 0,
    representatives: list[_Representative] | None = None,
) -> list[VideoFaceCandidate]:
    candidates: list[VideoFaceCandidate] = []
    target_representatives = representatives if representatives is not None else []
    for offset, observation in enumerate(observations, start=start_index + 1):
        candidate_id = f"face_{offset:04d}"
        image_path = output_dir / f"{candidate_id}.jpg"
        cv2.imwrite(str(image_path), observation.crop)
        target_representatives.append(
            _Representative(
                histogram=observation.histogram,
                matcher=_prepare_candidate_matcher(
                    face_matcher,
                    image_path,
                    observation.crop,
                ),
                track_ids=(
                    {observation.detection.track_id}
                    if observation.detection.track_id is not None
                    else set()
                ),
            )
        )
        candidates.append(
            VideoFaceCandidate(
                candidate_id=candidate_id,
                image_path=image_path,
                frame_index=observation.frame_index,
                confidence=observation.detection.confidence,
            )
        )
    return candidates


def _select_group_frame_observations(
    group_frames: list[list[_FaceObservation]],
    max_candidates: int,
) -> list[_FaceObservation]:
    if max_candidates <= 0 or not group_frames:
        return []
    best_frame = max(
        group_frames,
        key=lambda observations: (
            min(len(observations), max_candidates),
            sum(item.quality for item in observations)
            / max(1, len(observations)),
            min(item.detection.confidence for item in observations),
        ),
    )
    return sorted(
        sorted(best_frame, key=lambda item: item.quality, reverse=True)[:max_candidates],
        key=lambda item: item.detection.x1,
    )


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


def _is_low_quality_candidate(
    frame: np.ndarray,
    detection: Detection,
    crop: np.ndarray,
    sharpness: float,
) -> bool:
    height, width = frame.shape[:2]
    face_width = detection.x2 - detection.x1
    face_height = detection.y2 - detection.y1
    if min(face_width, face_height) < 40:
        return True
    crop_height, crop_width = crop.shape[:2]
    aspect_ratio = crop_width / max(1, crop_height)
    if aspect_ratio < 0.70 or aspect_ratio > 1.6:
        return True
    if _touches_frame_edge(detection, width, height):
        return True
    return sharpness < 8.0 and min(crop.shape[:2]) < 96


def _touches_frame_edge(detection: Detection, width: int, height: int) -> bool:
    margin = max(2, int(min(width, height) * 0.01))
    return (
        detection.x1 <= margin
        or detection.y1 <= margin
        or detection.x2 >= width - margin
        or detection.y2 >= height - margin
    )


def _candidate_quality(frame: np.ndarray, detection: Detection, sharpness: float) -> float:
    height, width = frame.shape[:2]
    face_area = max(1, (detection.x2 - detection.x1) * (detection.y2 - detection.y1))
    frame_area = max(1, width * height)
    size_score = min(1.0, face_area / frame_area * 12.0) * 100.0
    return detection.confidence * 100.0 + min(sharpness, 250.0) + size_score


def _keep_clear_observations(observations: list[_FaceObservation]) -> list[_FaceObservation]:
    if not observations:
        return []
    best_sharpness = max(observation.sharpness for observation in observations)
    minimum_sharpness = max(8.0, best_sharpness * 0.35)
    return [
        observation
        for observation in observations
        if observation.sharpness >= minimum_sharpness
    ]


def _sharpness(image: np.ndarray) -> float:
    if image.size == 0:
        return 0.0
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (96, 96), interpolation=cv2.INTER_AREA)
    return float(cv2.Laplacian(resized, cv2.CV_64F).var())


def _candidate_histogram(image: np.ndarray) -> np.ndarray:
    resized = cv2.resize(image, (96, 96), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
    histogram = cv2.calcHist([hsv], [0, 1], None, [32, 32], [0, 180, 0, 256])
    cv2.normalize(histogram, histogram, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
    return histogram


def _is_duplicate_observation(
    observation: _FaceObservation,
    representatives: list[_Representative],
    histogram_threshold: float,
    identity_threshold: float,
) -> bool:
    for representative in representatives:
        if _same_track(observation, representative):
            return True
        if (
            cv2.compareHist(
                observation.histogram,
                representative.histogram,
                cv2.HISTCMP_CORREL,
            )
            >= histogram_threshold
        ):
            return True
        if _matches_representative(
            observation.crop,
            representative.matcher,
            identity_threshold,
        ):
            return True
    return False


def _same_track(observation: _FaceObservation, representative: _Representative) -> bool:
    track_id = observation.detection.track_id
    return track_id is not None and track_id in representative.track_ids


def _matches_representative(
    crop: np.ndarray,
    matcher: PreparedFaceMatcher | None,
    identity_threshold: float,
) -> bool:
    if matcher is None or crop.size == 0:
        return False
    height, width = crop.shape[:2]
    detection = Detection("face", 0, 0, width, height, 1.0)
    try:
        return matcher.match_score(crop, detection) >= identity_threshold
    except Exception:
        return False


def _prepare_candidate_matcher(
    face_matcher: FaceIdentityMatcher | None,
    image_path: Path,
    crop: np.ndarray,
) -> PreparedFaceMatcher | None:
    if face_matcher is None:
        return None
    try:
        prepare_image = getattr(face_matcher, "prepare_image", None)
        if callable(prepare_image):
            return prepare_image(crop)
        return face_matcher.prepare(image_path)
    except (FaceIdentityError, cv2.error, OSError, ValueError):
        return None
