from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import cv2
import numpy as np


TARGET_SIZE = (1600, 900)
SOURCE_IMAGE = Path("samples/references/face_detected.png")
BOX_FILE = Path("samples/references/face_detected_boxes.json")
ASSET_DIR = Path("frontend/assets")
REPORT_DIR = Path("samples/reports")


@dataclass(frozen=True)
class FaceRegion:
    box: tuple[int, int, int, int]
    privacy_box: tuple[int, int, int, int]
    confidence: float
    is_reference: bool = False


FACE_REGIONS = [
    FaceRegion((503, 121, 798, 452), (508, 160, 793, 447), 0.91),
    FaceRegion((1597, 70, 1874, 388), (1602, 109, 1869, 383), 0.94, is_reference=True),
    FaceRegion((441, 690, 755, 1054), (446, 729, 750, 1049), 0.91),
    FaceRegion((985, 682, 1240, 985), (990, 721, 1235, 980), 0.90),
    FaceRegion((1435, 664, 1705, 966), (1440, 703, 1700, 961), 0.89),
]


def load_face_regions() -> list[FaceRegion]:
    if not BOX_FILE.exists():
        return FACE_REGIONS
    payload = json.loads(BOX_FILE.read_text(encoding="utf-8"))
    regions = []
    for index, item in enumerate(payload.get("regions", []), start=1):
        raw_box = item.get("box")
        if not isinstance(raw_box, list) or len(raw_box) != 4:
            raise ValueError(f"invalid box at region {index}: {raw_box!r}")
        box = parse_box(raw_box, f"region {index} box")
        privacy_box = parse_box(item.get("privacy_box", raw_box), f"region {index} privacy_box")
        if box[2] <= box[0] or box[3] <= box[1]:
            raise ValueError(f"invalid box dimensions at region {index}: {raw_box!r}")
        if privacy_box[2] <= privacy_box[0] or privacy_box[3] <= privacy_box[1]:
            raise ValueError(f"invalid privacy box dimensions at region {index}: {raw_box!r}")
        regions.append(
            FaceRegion(
                box=box,
                privacy_box=privacy_box,
                confidence=float(item.get("confidence", 0.9)),
                is_reference=bool(item.get("is_reference", False)),
            )
        )
    if not regions:
        raise ValueError(f"no regions found in {BOX_FILE}")
    return regions


def parse_box(raw_box, name: str) -> tuple[int, int, int, int]:
    if not isinstance(raw_box, list) or len(raw_box) != 4:
        raise ValueError(f"invalid {name}: {raw_box!r}")
    x1, y1, x2, y2 = [int(round(float(value))) for value in raw_box]
    return x1, y1, x2, y2


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


def scaled_box(box: tuple[int, int, int, int], scale: float, offset_x: int, offset_y: int) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = box
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


def draw_smile_emoji(image: np.ndarray, box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = clip_box(box, image.shape[1], image.shape[0])
    width = x2 - x1
    height = y2 - y1
    center = (x1 + width // 2, y1 + height // 2)
    radius = max(44, int(max(width, height) * 0.58))

    overlay = image.copy()
    cv2.circle(overlay, center, radius, (24, 207, 255), -1, lineType=cv2.LINE_AA)
    cv2.circle(overlay, (center[0] - radius // 4, center[1] - radius // 4), radius // 2, (92, 235, 255), -1)
    image[:] = cv2.addWeighted(overlay, 0.96, image, 0.04, 0)

    edge = (18, 142, 224)
    dark = (34, 41, 49)
    white = (255, 255, 255)
    cv2.circle(image, center, radius, edge, max(4, radius // 24), lineType=cv2.LINE_AA)
    cv2.ellipse(
        image,
        (center[0], center[1] - radius // 3),
        (int(radius * 0.62), int(radius * 0.26)),
        0,
        190,
        350,
        (116, 246, 255),
        max(4, radius // 18),
        cv2.LINE_AA,
    )
    eye_y = center[1] - int(radius * 0.18)
    eye_dx = int(radius * 0.32)
    eye_size = (max(8, radius // 8), max(10, radius // 6))
    cv2.ellipse(image, (center[0] - eye_dx, eye_y), eye_size, 0, 0, 360, dark, -1, cv2.LINE_AA)
    cv2.ellipse(image, (center[0] + eye_dx, eye_y), eye_size, 0, 0, 360, dark, -1, cv2.LINE_AA)
    cv2.circle(image, (center[0] - eye_dx - radius // 18, eye_y - radius // 20), max(2, radius // 28), white, -1)
    cv2.circle(image, (center[0] + eye_dx - radius // 18, eye_y - radius // 20), max(2, radius // 28), white, -1)
    cv2.ellipse(
        image,
        (center[0], center[1] + int(radius * 0.15)),
        (int(radius * 0.44), int(radius * 0.32)),
        0,
        18,
        162,
        dark,
        max(6, radius // 13),
        cv2.LINE_AA,
    )


def clip_box(box: tuple[int, int, int, int], width: int, height: int) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = box
    return max(0, x1), max(0, y1), min(width, x2), min(height, y2)


def make_showcase(mode: str) -> np.ndarray:
    canvas, scale, offset_x, offset_y = fit_to_canvas(read_source())
    for region in load_face_regions():
        privacy_box = scaled_box(region.privacy_box, scale, offset_x, offset_y)
        if mode == "original":
            continue
        if mode == "blur":
            blur_box(canvas, privacy_box)
            continue
        if mode == "preserve" and region.is_reference:
            continue
        if mode == "character" and region.is_reference:
            draw_smile_emoji(canvas, privacy_box)
            continue
        blur_box(canvas, privacy_box)
    return canvas


def write_contact_sheet(images: dict[str, np.ndarray]) -> None:
    thumb_width, thumb_height = 640, 360
    rows: list[np.ndarray] = []
    labels = {
        "original": "DETECT",
        "blur": "BLUR AFTER",
        "preserve": "REFERENCE KEEP",
        "character": "SMILE EMOJI",
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
