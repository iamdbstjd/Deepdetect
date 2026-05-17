from __future__ import annotations

from pathlib import Path
import re

import cv2
import numpy as np


class CharacterAssetStore:
    def __init__(self, assets_dir: Path):
        self.assets_dir = assets_dir

    def load(self, character_id: str | None) -> np.ndarray:
        asset_path = self._asset_path(character_id or "default_emoji")
        if asset_path.exists():
            image = cv2.imread(str(asset_path), cv2.IMREAD_UNCHANGED)
            if image is not None and image.size:
                return _ensure_bgra(image)
        return self._default_emoji()

    def _asset_path(self, character_id: str) -> Path:
        safe_id = re.sub(r"[^A-Za-z0-9_-]+", "_", character_id).strip("_")
        safe_id = safe_id or "default_emoji"
        return self.assets_dir / f"{safe_id}.png"

    @staticmethod
    def _default_emoji() -> np.ndarray:
        size = 512
        image = np.zeros((size, size, 4), dtype=np.uint8)
        yy, xx = np.mgrid[0:size, 0:size]
        center = (size - 1) / 2
        radius = 222
        distance = np.sqrt((xx - center) ** 2 + (yy - center) ** 2)
        edge_alpha = np.clip((radius + 2 - distance) / 5, 0, 1)
        mask = edge_alpha > 0

        vertical = yy / (size - 1)
        radial = np.clip(distance / radius, 0, 1)
        blue = 26 - 18 * vertical
        green = 224 - 42 * vertical - 22 * radial
        red = 255 - 4 * vertical
        image[:, :, 0] = np.where(mask, blue, 0).astype(np.uint8)
        image[:, :, 1] = np.where(mask, green, 0).astype(np.uint8)
        image[:, :, 2] = np.where(mask, red, 0).astype(np.uint8)
        image[:, :, 3] = (edge_alpha * 255).astype(np.uint8)

        cv2.circle(image, (256, 256), 224, (18, 142, 224, 255), 8, lineType=cv2.LINE_AA)
        cv2.ellipse(image, (256, 174), (142, 66), 0, 190, 350, (110, 246, 255, 255), 10)
        cv2.ellipse(image, (184, 212), (27, 36), 0, 0, 360, (34, 41, 49, 255), -1, cv2.LINE_AA)
        cv2.ellipse(image, (328, 212), (27, 36), 0, 0, 360, (34, 41, 49, 255), -1, cv2.LINE_AA)
        cv2.circle(image, (174, 200), 7, (255, 255, 255, 255), -1, lineType=cv2.LINE_AA)
        cv2.circle(image, (318, 200), 7, (255, 255, 255, 255), -1, lineType=cv2.LINE_AA)
        cv2.ellipse(image, (256, 292), (98, 72), 0, 18, 162, (34, 41, 49, 255), 18, cv2.LINE_AA)
        return cv2.resize(image, (256, 256), interpolation=cv2.INTER_AREA)


def _ensure_bgra(image: np.ndarray) -> np.ndarray:
    if image.ndim != 3:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGRA)
    if image.shape[2] == 4:
        return image
    if image.shape[2] == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
    raise ValueError("unsupported character asset channel count")
