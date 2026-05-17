from __future__ import annotations

from pathlib import Path

import cv2


def read_frame(video: Path, frame_index: int = 30):
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


def export_jpg(source: Path, output: Path) -> None:
    frame = read_frame(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 88]):
        raise RuntimeError(f"cannot write image: {output}")


def main() -> int:
    pairs = {
        "showcase_original.jpg": Path("samples/videos/akiyo_short.mp4"),
        "showcase_blur.jpg": Path("samples/outputs/akiyo_blur.mp4"),
        "showcase_preserve.jpg": Path("samples/outputs/akiyo_preserve.mp4"),
        "showcase_character.jpg": Path("samples/outputs/akiyo_character.mp4"),
    }
    for name, source in pairs.items():
        export_jpg(source, Path("frontend/assets") / name)
        print(Path("frontend/assets") / name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
