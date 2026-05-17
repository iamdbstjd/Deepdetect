from __future__ import annotations

from pathlib import Path
import re

import cv2
import numpy as np


class CharacterAssetStore:
    def __init__(self, assets_dir: Path):
        self.assets_dir = assets_dir

    def load(self, character_id: str | None) -> np.ndarray:
        asset_path = self._asset_path(character_id or "default_mask")
        if asset_path.exists():
            image = cv2.imread(str(asset_path), cv2.IMREAD_UNCHANGED)
            if image is not None and image.size:
                return _ensure_bgra(image)
        return self._default_mask()

    def _asset_path(self, character_id: str) -> Path:
        safe_id = re.sub(r"[^A-Za-z0-9_-]+", "_", character_id).strip("_")
        safe_id = safe_id or "default_mask"
        return self.assets_dir / f"{safe_id}.png"

    @staticmethod
    def _default_mask() -> np.ndarray:
        size = 512
        image = np.zeros((size, size, 4), dtype=np.uint8)
        yy, xx = np.mgrid[0:size, 0:size]
        center = (size - 1) / 2
        radius = 226
        distance = np.sqrt((xx - center) ** 2 + (yy - center) ** 2)
        edge_alpha = np.clip((radius + 2 - distance) / 5, 0, 1)
        mask = edge_alpha > 0

        radial = np.clip(distance / radius, 0, 1)
        image[:, :, 0] = np.where(mask, 104 - 22 * radial, 0).astype(np.uint8)
        image[:, :, 1] = np.where(mask, 129 - 18 * radial, 0).astype(np.uint8)
        image[:, :, 2] = np.where(mask, 16 - 8 * radial, 0).astype(np.uint8)
        image[:, :, 3] = (edge_alpha * 255).astype(np.uint8)

        white = (246, 255, 255, 255)
        dark = (44, 70, 8, 255)
        cv2.circle(image, (256, 256), 226, white, 9, lineType=cv2.LINE_AA)
        cv2.circle(image, (190, 214), 20, white, -1, lineType=cv2.LINE_AA)
        cv2.circle(image, (322, 214), 20, white, -1, lineType=cv2.LINE_AA)
        cv2.ellipse(image, (256, 292), (88, 56), 0, 18, 162, white, 13, cv2.LINE_AA)
        cv2.putText(
            image,
            "d",
            (226, 382),
            cv2.FONT_HERSHEY_SIMPLEX,
            2.25,
            dark,
            10,
            cv2.LINE_AA,
        )
        return cv2.resize(image, (256, 256), interpolation=cv2.INTER_AREA)


def _ensure_bgra(image: np.ndarray) -> np.ndarray:
    if image.ndim != 3:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGRA)
    if image.shape[2] == 4:
        return image
    if image.shape[2] == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
    raise ValueError("unsupported character asset channel count")
