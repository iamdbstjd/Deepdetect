from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from backend.app.vision.detections import Detection


@dataclass(frozen=True)
class OverlayInstruction:
    detection: Detection
    image: np.ndarray


class PrivacyRenderer:
    def __init__(
        self,
        face_padding: float = 0.18,
        plate_padding: float = 0.12,
        blur_strength: int = 45,
    ):
        self.face_padding = face_padding
        self.plate_padding = plate_padding
        self.blur_strength = blur_strength

    def render(
        self,
        frame: np.ndarray,
        detections: list[Detection],
        overlays: list[OverlayInstruction] | None = None,
    ) -> np.ndarray:
        output = frame.copy()
        height, width = output.shape[:2]
        for detection in detections:
            padding = self.face_padding if detection.kind == "face" else self.plate_padding
            box = detection.clipped(width, height, padding)
            if not box.is_valid:
                continue
            self._blur_box(output, box)
        for overlay in overlays or []:
            box = overlay.detection.clipped(width, height, self.face_padding)
            if not box.is_valid:
                continue
            self._overlay_image(output, box, overlay.image)
        return output

    def _blur_box(self, frame: np.ndarray, detection: Detection) -> None:
        roi = frame[detection.y1 : detection.y2, detection.x1 : detection.x2]
        if roi.size == 0:
            return
        kernel = self._kernel_size(roi.shape[1], roi.shape[0])
        blurred = cv2.GaussianBlur(roi, (kernel, kernel), 0)
        frame[detection.y1 : detection.y2, detection.x1 : detection.x2] = blurred

    def _kernel_size(self, width: int, height: int) -> int:
        base = max(7, min(self.blur_strength, max(width, height) // 2))
        return base if base % 2 == 1 else base + 1

    @staticmethod
    def _overlay_image(frame: np.ndarray, detection: Detection, image: np.ndarray) -> None:
        if image.ndim != 3 or image.shape[2] not in {3, 4}:
            return
        source_height, source_width = image.shape[:2]
        target_width = detection.x2 - detection.x1
        target_height = detection.y2 - detection.y1
        if source_width <= 0 or source_height <= 0 or target_width <= 0 or target_height <= 0:
            return

        scale = max(target_width / source_width, target_height / source_height)
        overlay_width = max(1, int(round(source_width * scale)))
        overlay_height = max(1, int(round(source_height * scale)))
        interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
        overlay = cv2.resize(image, (overlay_width, overlay_height), interpolation=interpolation)

        center_x = (detection.x1 + detection.x2) // 2
        center_y = (detection.y1 + detection.y2) // 2
        x1 = center_x - overlay_width // 2
        y1 = center_y - overlay_height // 2
        x2 = x1 + overlay_width
        y2 = y1 + overlay_height

        frame_height, frame_width = frame.shape[:2]
        clipped_x1 = max(0, x1)
        clipped_y1 = max(0, y1)
        clipped_x2 = min(frame_width, x2)
        clipped_y2 = min(frame_height, y2)
        if clipped_x2 <= clipped_x1 or clipped_y2 <= clipped_y1:
            return

        source_x1 = clipped_x1 - x1
        source_y1 = clipped_y1 - y1
        source_x2 = source_x1 + (clipped_x2 - clipped_x1)
        source_y2 = source_y1 + (clipped_y2 - clipped_y1)
        clipped_overlay = overlay[source_y1:source_y2, source_x1:source_x2]
        roi = frame[clipped_y1:clipped_y2, clipped_x1:clipped_x2]

        if clipped_overlay.shape[2] == 4:
            color = clipped_overlay[:, :, :3].astype(np.float32)
            alpha = clipped_overlay[:, :, 3:4].astype(np.float32) / 255.0
            blended = color * alpha + roi.astype(np.float32) * (1.0 - alpha)
            frame[clipped_y1:clipped_y2, clipped_x1:clipped_x2] = blended.astype(np.uint8)
            return
        if clipped_overlay.shape[2] == 3:
            frame[clipped_y1:clipped_y2, clipped_x1:clipped_x2] = clipped_overlay
