from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class Detection:
    kind: str
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float
    label: str = ""
    track_id: int | None = None
    observed: bool = True
    missed: int = 0

    def clipped(self, width: int, height: int, padding_ratio: float = 0.0) -> "Detection":
        pad_x = int((self.x2 - self.x1) * padding_ratio)
        pad_y = int((self.y2 - self.y1) * padding_ratio)
        return Detection(
            kind=self.kind,
            x1=max(0, self.x1 - pad_x),
            y1=max(0, self.y1 - pad_y),
            x2=min(width, self.x2 + pad_x),
            y2=min(height, self.y2 + pad_y),
            confidence=self.confidence,
            label=self.label,
            track_id=self.track_id,
            observed=self.observed,
            missed=self.missed,
        )

    @property
    def is_valid(self) -> bool:
        return self.x2 > self.x1 and self.y2 > self.y1


class RegionDetector(Protocol):
    def detect(self, frame: np.ndarray) -> list[Detection]:
        ...


class NoopDetector:
    def detect(self, frame: np.ndarray) -> list[Detection]:
        return []


class StaticDetector:
    def __init__(self, detections: list[Detection]):
        self.detections = detections

    def detect(self, frame: np.ndarray) -> list[Detection]:
        return self.detections
