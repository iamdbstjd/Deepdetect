from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


POSE_FRONT = "front"
POSE_LEFT_45 = "left_45"
POSE_RIGHT_45 = "right_45"
POSE_LEFT_PROFILE = "left_profile"
POSE_RIGHT_PROFILE = "right_profile"
POSE_NO_FACE = "no_face"
POSE_UNKNOWN = "unknown"


class FacePoseError(RuntimeError):
    pass


@dataclass(frozen=True)
class PoseObservation:
    x: int
    y: int
    width: int
    height: int
    score: float = 1.0

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def center_x(self) -> float:
        return self.x + self.width / 2

    def to_box(self) -> dict[str, int]:
        return {
            "x1": self.x,
            "y1": self.y,
            "x2": self.x + self.width,
            "y2": self.y + self.height,
        }


@dataclass(frozen=True)
class FacePoseEstimate:
    detected: bool
    pose: str
    yaw: float
    confidence: float
    box: dict[str, int] | None = None

    def to_public_dict(self) -> dict[str, object]:
        return {
            "detected": self.detected,
            "pose": self.pose,
            "yaw": self.yaw,
            "confidence": self.confidence,
            "box": self.box,
        }


class HaarFacePoseEstimator:
    """Estimate coarse face direction with bundled OpenCV cascades.

    This is a webcam enrollment guide, not a biometric head-pose model. It
    classifies enough coarse direction states to prevent accidental captures in
    the wrong step without adding a new model dependency.
    """

    def __init__(self) -> None:
        cascade_dir = Path(cv2.data.haarcascades)
        self.frontal = _load_cascade(cascade_dir / "haarcascade_frontalface_default.xml")
        self.profile = _load_cascade(cascade_dir / "haarcascade_profileface.xml")

    def estimate(self, frame: np.ndarray) -> FacePoseEstimate:
        if frame is None or frame.size == 0:
            raise FacePoseError("empty frame")
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        frame_width = int(gray.shape[1])

        frontal = _best_observation(_detect(self.frontal, gray, min_size=(48, 48)))
        left_profile = _best_observation(_detect(self.profile, gray, min_size=(44, 44)))
        right_profile = _best_observation(
            _mirror_observations(
                _detect(self.profile, cv2.flip(gray, 1), min_size=(44, 44)),
                frame_width,
            )
        )
        return classify_pose_observations(frontal, left_profile, right_profile, frame_width)


def classify_pose_observations(
    frontal: PoseObservation | None,
    left_profile: PoseObservation | None,
    right_profile: PoseObservation | None,
    frame_width: int,
) -> FacePoseEstimate:
    profiles = [
        (POSE_LEFT_PROFILE, -72.0, left_profile),
        (POSE_RIGHT_PROFILE, 72.0, right_profile),
    ]
    valid_profiles = [(pose, yaw, observation) for pose, yaw, observation in profiles if observation]

    if frontal is None and not valid_profiles:
        return FacePoseEstimate(False, POSE_NO_FACE, 0.0, 0.0)

    if frontal is None:
        pose, yaw, profile = max(valid_profiles, key=lambda item: item[2].area * item[2].score)
        return FacePoseEstimate(True, pose, yaw, _confidence(profile), profile.to_box())

    if valid_profiles:
        pose, yaw, profile = max(valid_profiles, key=lambda item: item[2].area * item[2].score)
        area_ratio = profile.area / max(1, frontal.area)
        if area_ratio >= 0.42:
            oblique_pose = POSE_LEFT_45 if pose == POSE_LEFT_PROFILE else POSE_RIGHT_45
            oblique_yaw = -43.0 if pose == POSE_LEFT_PROFILE else 43.0
            confidence = max(_confidence(frontal), _confidence(profile)) * 0.92
            return FacePoseEstimate(True, oblique_pose, oblique_yaw, confidence, profile.to_box())

    center_offset = (frontal.center_x - frame_width / 2) / max(1, frame_width / 2)
    if center_offset < -0.22:
        return FacePoseEstimate(True, POSE_LEFT_45, -34.0, _confidence(frontal) * 0.72, frontal.to_box())
    if center_offset > 0.22:
        return FacePoseEstimate(True, POSE_RIGHT_45, 34.0, _confidence(frontal) * 0.72, frontal.to_box())
    return FacePoseEstimate(True, POSE_FRONT, 0.0, _confidence(frontal), frontal.to_box())


def _load_cascade(path: Path) -> cv2.CascadeClassifier:
    classifier = cv2.CascadeClassifier(str(path))
    if classifier.empty():
        raise FacePoseError(f"OpenCV cascade unavailable: {path.name}")
    return classifier


def _detect(
    classifier: cv2.CascadeClassifier,
    gray: np.ndarray,
    min_size: tuple[int, int],
) -> list[PoseObservation]:
    try:
        rects, _, weights = classifier.detectMultiScale3(
            gray,
            scaleFactor=1.08,
            minNeighbors=4,
            minSize=min_size,
            outputRejectLevels=True,
        )
    except cv2.error:
        rects = classifier.detectMultiScale(
            gray,
            scaleFactor=1.08,
            minNeighbors=4,
            minSize=min_size,
        )
        weights = [1.0] * len(rects)
    return [
        PoseObservation(int(x), int(y), int(w), int(h), float(weight))
        for (x, y, w, h), weight in zip(rects, weights)
    ]


def _mirror_observations(observations: list[PoseObservation], frame_width: int) -> list[PoseObservation]:
    return [
        PoseObservation(
            x=max(0, frame_width - observation.x - observation.width),
            y=observation.y,
            width=observation.width,
            height=observation.height,
            score=observation.score,
        )
        for observation in observations
    ]


def _best_observation(observations: list[PoseObservation]) -> PoseObservation | None:
    if not observations:
        return None
    return max(observations, key=lambda observation: observation.area * observation.score)


def _confidence(observation: PoseObservation) -> float:
    score_component = min(0.28, max(0.0, observation.score) / 20.0)
    size_component = min(0.28, observation.area / 90000.0)
    return round(min(0.98, 0.52 + score_component + size_component), 3)
