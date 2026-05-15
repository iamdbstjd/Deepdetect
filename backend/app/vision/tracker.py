from __future__ import annotations

from dataclasses import dataclass

from backend.app.vision.detections import Detection


@dataclass
class _Track:
    track_id: int
    kind: str
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    label: str
    missed: int = 0

    def as_detection(self, observed: bool) -> Detection:
        return Detection(
            kind=self.kind,
            x1=round(self.x1),
            y1=round(self.y1),
            x2=round(self.x2),
            y2=round(self.y2),
            confidence=self.confidence,
            label=self.label,
            track_id=self.track_id,
            observed=observed,
            missed=self.missed,
        )


class DetectionTracker:
    def __init__(
        self,
        iou_threshold: float = 0.3,
        smoothing_alpha: float = 0.55,
        max_missing: int = 2,
    ):
        if not 0.0 <= smoothing_alpha <= 1.0:
            raise ValueError("smoothing_alpha must be between 0 and 1")
        self.iou_threshold = iou_threshold
        self.smoothing_alpha = smoothing_alpha
        self.max_missing = max_missing
        self._next_track_id = 1
        self._tracks: dict[int, _Track] = {}

    def reset(self) -> None:
        self._next_track_id = 1
        self._tracks.clear()

    def update(self, detections: list[Detection]) -> list[Detection]:
        matches = self._match(detections)
        matched_track_ids = {track_id for track_id, _index in matches}
        matched_detection_indexes = {index for _track_id, index in matches}
        output: list[Detection] = []

        for track_id, detection_index in matches:
            track = self._tracks[track_id]
            detection = detections[detection_index]
            self._update_track(track, detection)
            output.append(track.as_detection(observed=True))

        for index, detection in enumerate(detections):
            if index in matched_detection_indexes:
                continue
            track = self._new_track(detection)
            output.append(track.as_detection(observed=True))

        for track_id, track in list(self._tracks.items()):
            if track_id in matched_track_ids:
                continue
            if any(d.track_id == track_id for d in output):
                continue
            track.missed += 1
            track.confidence *= 0.5
            if track.missed > self.max_missing:
                del self._tracks[track_id]
                continue
            output.append(track.as_detection(observed=False))

        return sorted(output, key=lambda detection: (detection.kind, detection.track_id or 0))

    def _match(self, detections: list[Detection]) -> list[tuple[int, int]]:
        candidates: list[tuple[float, int, int]] = []
        for track_id, track in self._tracks.items():
            track_detection = track.as_detection(observed=True)
            for index, detection in enumerate(detections):
                if track.kind != detection.kind:
                    continue
                score = iou(track_detection, detection)
                if score >= self.iou_threshold:
                    candidates.append((score, track_id, index))

        matches: list[tuple[int, int]] = []
        used_tracks: set[int] = set()
        used_detections: set[int] = set()
        for _score, track_id, index in sorted(candidates, reverse=True):
            if track_id in used_tracks or index in used_detections:
                continue
            used_tracks.add(track_id)
            used_detections.add(index)
            matches.append((track_id, index))
        return matches

    def _new_track(self, detection: Detection) -> _Track:
        track = _Track(
            track_id=self._next_track_id,
            kind=detection.kind,
            x1=float(detection.x1),
            y1=float(detection.y1),
            x2=float(detection.x2),
            y2=float(detection.y2),
            confidence=detection.confidence,
            label=detection.label,
        )
        self._tracks[track.track_id] = track
        self._next_track_id += 1
        return track

    def _update_track(self, track: _Track, detection: Detection) -> None:
        alpha = self.smoothing_alpha
        inverse = 1.0 - alpha
        track.x1 = track.x1 * inverse + detection.x1 * alpha
        track.y1 = track.y1 * inverse + detection.y1 * alpha
        track.x2 = track.x2 * inverse + detection.x2 * alpha
        track.y2 = track.y2 * inverse + detection.y2 * alpha
        track.confidence = detection.confidence
        track.label = detection.label
        track.missed = 0


def iou(left: Detection, right: Detection) -> float:
    x1 = max(left.x1, right.x1)
    y1 = max(left.y1, right.y1)
    x2 = min(left.x2, right.x2)
    y2 = min(left.y2, right.y2)
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    if intersection == 0:
        return 0.0
    left_area = max(0, left.x2 - left.x1) * max(0, left.y2 - left.y1)
    right_area = max(0, right.x2 - right.x1) * max(0, right.y2 - right.y1)
    union = left_area + right_area - intersection
    return intersection / union if union else 0.0
