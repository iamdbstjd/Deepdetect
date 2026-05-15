from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np


def read_frame(video: Path, frame_index: int) -> np.ndarray:
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise RuntimeError(f"cannot open video: {video}")
    try:
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = capture.read()
        if not ok or frame is None:
            raise RuntimeError(f"cannot read frame {frame_index} from {video}")
        return frame
    finally:
        capture.release()


def normalize_size(frame: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    return cv2.resize(frame, size, interpolation=cv2.INTER_AREA)


def add_label(frame: np.ndarray, label: str) -> np.ndarray:
    output = frame.copy()
    cv2.rectangle(output, (0, 0), (output.shape[1], 26), (20, 20, 20), -1)
    cv2.putText(
        output,
        label,
        (8, 18),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a contact sheet for sample QA.")
    parser.add_argument("--original", type=Path, default=Path("samples/videos/akiyo_short.mp4"))
    parser.add_argument("--blur", type=Path, default=Path("samples/outputs/akiyo_blur.mp4"))
    parser.add_argument("--preserve", type=Path, default=Path("samples/outputs/akiyo_preserve.mp4"))
    parser.add_argument("--character", type=Path, default=Path("samples/outputs/akiyo_character.mp4"))
    parser.add_argument("--output", type=Path, default=Path("samples/reports/akiyo_contact_sheet.jpg"))
    parser.add_argument("--frames", default="0,30,60,89")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    frame_indexes = [int(value.strip()) for value in args.frames.split(",") if value.strip()]
    videos = [
        ("original", args.original),
        ("blur", args.blur),
        ("preserve", args.preserve),
        ("character", args.character),
    ]
    rows = []
    target_size: tuple[int, int] | None = None
    for label, video in videos:
        cells = []
        for frame_index in frame_indexes:
            frame = read_frame(video, frame_index)
            if target_size is None:
                target_size = (frame.shape[1], frame.shape[0])
            cells.append(add_label(normalize_size(frame, target_size), f"{label} f{frame_index}"))
        rows.append(np.concatenate(cells, axis=1))
    sheet = np.concatenate(rows, axis=0)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(args.output), sheet):
        raise RuntimeError(f"cannot write contact sheet: {args.output}")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
