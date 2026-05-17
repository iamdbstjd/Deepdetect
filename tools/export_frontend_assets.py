from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


TARGET_SIZE = (1600, 900)
SOURCE_IMAGE = Path("samples/references/group_sample.jpg")
ASSET_DIR = Path("frontend/assets")
REPORT_DIR = Path("samples/reports")


@dataclass(frozen=True)
class FaceRegion:
    box: tuple[int, int, int, int]
    confidence: float
    is_reference: bool = False


FACE_REGIONS = [
    FaceRegion((188, 360, 430, 612), 0.91),
    FaceRegion((260, 66, 460, 292), 0.88),
    FaceRegion((520, 384, 704, 574), 0.90),
    FaceRegion((754, 338, 942, 526), 0.89),
    FaceRegion((836, 38, 1096, 306), 0.94, is_reference=True),
]


def read_source() -> np.ndarray:
    image = cv2.imread(str(SOURCE_IMAGE))
    if image is None:
        raise RuntimeError(f"cannot read image: {SOURCE_IMAGE}")
    return image


def fit_to_canvas(source: np.ndarray) -> tuple[np.ndarray, float, int, int]:
    target_width, target_height = TARGET_SIZE
    source_height, source_width = source.shape[:2]

    background_scale = max(target_width / source_width, target_height / source_height)
    background_size = (
        int(round(source_width * background_scale)),
        int(round(source_height * background_scale)),
    )
    background = cv2.resize(source, background_size, interpolation=cv2.INTER_CUBIC)
    crop_x = max(0, (background.shape[1] - target_width) // 2)
    crop_y = max(0, (background.shape[0] - target_height) // 2)
    background = background[crop_y : crop_y + target_height, crop_x : crop_x + target_width]
    background = cv2.GaussianBlur(background, (45, 45), 0)
    background = cv2.addWeighted(background, 0.62, np.zeros_like(background), 0.38, 0)

    foreground_scale = min(target_width / source_width, target_height / source_height)
    foreground_size = (
        int(round(source_width * foreground_scale)),
        int(round(source_height * foreground_scale)),
    )
    foreground = cv2.resize(source, foreground_size, interpolation=cv2.INTER_AREA)
    offset_x = (target_width - foreground.shape[1]) // 2
    offset_y = (target_height - foreground.shape[0]) // 2
    output = background.copy()
    output[offset_y : offset_y + foreground.shape[0], offset_x : offset_x + foreground.shape[1]] = foreground
    return output, foreground_scale, offset_x, offset_y


def scaled_box(region: FaceRegion, scale: float, offset_x: int, offset_y: int) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = region.box
    return (
        int(round(x1 * scale + offset_x)),
        int(round(y1 * scale + offset_y)),
        int(round(x2 * scale + offset_x)),
        int(round(y2 * scale + offset_y)),
    )


def blur_box(image: np.ndarray, box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = clip_box(box, image.shape[1], image.shape[0])
    roi = image[y1:y2, x1:x2]
    if roi.size == 0:
        return
    kernel = max(35, min(91, max(roi.shape[:2]) // 2))
    if kernel % 2 == 0:
        kernel += 1
    blurred = cv2.GaussianBlur(roi, (kernel, kernel), 0)
    pixelated = cv2.resize(roi, (max(1, roi.shape[1] // 12), max(1, roi.shape[0] // 12)))
    pixelated = cv2.resize(pixelated, (roi.shape[1], roi.shape[0]), interpolation=cv2.INTER_NEAREST)
    image[y1:y2, x1:x2] = cv2.addWeighted(blurred, 0.72, pixelated, 0.28, 0)


def draw_privacy_mask(image: np.ndarray, box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = clip_box(box, image.shape[1], image.shape[0])
    width = x2 - x1
    height = y2 - y1
    center = (x1 + width // 2, y1 + height // 2)
    axes = (max(36, int(width * 0.56)), max(42, int(height * 0.52)))

    overlay = image.copy()
    teal = (114, 124, 12)
    teal_dark = (64, 78, 8)
    white = (245, 255, 255)
    cv2.ellipse(overlay, center, axes, 0, 0, 360, teal, -1)
    cv2.ellipse(overlay, center, axes, 0, 0, 360, white, 5)
    image[:] = cv2.addWeighted(overlay, 0.94, image, 0.06, 0)

    eye_y = center[1] - int(axes[1] * 0.18)
    eye_dx = int(axes[0] * 0.32)
    eye_radius = max(7, int(axes[0] * 0.09))
    cv2.circle(image, (center[0] - eye_dx, eye_y), eye_radius, white, -1)
    cv2.circle(image, (center[0] + eye_dx, eye_y), eye_radius, white, -1)
    cv2.ellipse(
        image,
        (center[0], center[1] + int(axes[1] * 0.16)),
        (int(axes[0] * 0.34), int(axes[1] * 0.22)),
        0,
        12,
        168,
        white,
        5,
    )
    cv2.putText(
        image,
        "d",
        (center[0] - int(axes[0] * 0.14), center[1] + int(axes[1] * 0.62)),
        cv2.FONT_HERSHEY_SIMPLEX,
        max(1.0, axes[0] / 70),
        teal_dark,
        max(3, int(axes[0] * 0.055)),
        cv2.LINE_AA,
    )


def draw_detection_box(
    image: np.ndarray,
    box: tuple[int, int, int, int],
    label: str,
    color: tuple[int, int, int],
) -> None:
    x1, y1, x2, y2 = clip_box(box, image.shape[1], image.shape[0])
    thickness = 4
    cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.62
    text_thickness = 2
    (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, text_thickness)
    label_y1 = max(0, y1 - text_height - baseline - 12)
    label_y2 = label_y1 + text_height + baseline + 12
    label_x2 = min(image.shape[1], x1 + text_width + 18)
    cv2.rectangle(image, (x1, label_y1), (label_x2, label_y2), color, -1)
    cv2.putText(
        image,
        label,
        (x1 + 9, label_y2 - baseline - 6),
        font,
        font_scale,
        (255, 255, 255),
        text_thickness,
        cv2.LINE_AA,
    )


def clip_box(box: tuple[int, int, int, int], width: int, height: int) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = box
    return max(0, x1), max(0, y1), min(width, x2), min(height, y2)


def make_showcase(mode: str) -> np.ndarray:
    canvas, scale, offset_x, offset_y = fit_to_canvas(read_source())
    green = (114, 124, 12)
    blue = (235, 117, 37)
    orange = (0, 119, 217)

    for region in FACE_REGIONS:
        box = scaled_box(region, scale, offset_x, offset_y)
        if mode == "original":
            draw_detection_box(canvas, box, f"FACE {region.confidence:.2f}", blue)
            continue
        if mode == "blur":
            blur_box(canvas, box)
            draw_detection_box(canvas, box, "BLUR FACE", orange)
            continue
        if mode == "preserve" and region.is_reference:
            draw_detection_box(canvas, box, "REFERENCE KEEP", green)
            continue
        if mode == "character" and region.is_reference:
            draw_privacy_mask(canvas, box)
            draw_detection_box(canvas, box, "PRIVACY MASK", green)
            continue
        blur_box(canvas, box)
        draw_detection_box(canvas, box, "ANONYMIZED", orange)
    return canvas


def write_contact_sheet(images: dict[str, np.ndarray]) -> None:
    thumb_width, thumb_height = 640, 360
    rows: list[np.ndarray] = []
    labels = {
        "original": "DETECT",
        "blur": "BLUR AFTER",
        "preserve": "REFERENCE KEEP",
        "character": "PRIVACY MASK",
    }
    for left_key, right_key in [("original", "blur"), ("preserve", "character")]:
        row_images = []
        for key in [left_key, right_key]:
            thumb = cv2.resize(images[key], (thumb_width, thumb_height), interpolation=cv2.INTER_AREA)
            cv2.rectangle(thumb, (0, 0), (thumb_width, 44), (13, 20, 24), -1)
            cv2.putText(
                thumb,
                labels[key],
                (18, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.72,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            row_images.append(thumb)
        rows.append(np.hstack(row_images))
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(REPORT_DIR / "group_showcase_contact_sheet.jpg"), np.vstack(rows))


def main() -> int:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    images = {
        "original": make_showcase("original"),
        "blur": make_showcase("blur"),
        "preserve": make_showcase("preserve"),
        "character": make_showcase("character"),
    }
    outputs = {
        "showcase_original.jpg": images["original"],
        "showcase_blur.jpg": images["blur"],
        "showcase_preserve.jpg": images["preserve"],
        "showcase_character.jpg": images["character"],
    }
    for name, image in outputs.items():
        path = ASSET_DIR / name
        if not cv2.imwrite(str(path), image, [int(cv2.IMWRITE_JPEG_QUALITY), 90]):
            raise RuntimeError(f"cannot write image: {path}")
        print(path)
    write_contact_sheet(images)
    print(REPORT_DIR / "group_showcase_contact_sheet.jpg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
