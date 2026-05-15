from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.config import get_settings  # noqa: E402
from backend.app.vision.yolo_detector import build_detector  # noqa: E402


def sharpness(image) -> float:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Measure blur strength in detected face regions.")
    parser.add_argument("--original", type=Path, default=Path("samples/videos/akiyo_short.mp4"))
    parser.add_argument("--blurred", type=Path, default=Path("samples/outputs/akiyo_blur.mp4"))
    parser.add_argument("--report", type=Path, default=Path("samples/reports/akiyo_blur_quality.json"))
    parser.add_argument("--max-frames", type=int, default=90)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = get_settings()
    detector = build_detector(settings)
    original_capture = cv2.VideoCapture(str(args.original))
    blurred_capture = cv2.VideoCapture(str(args.blurred))
    if not original_capture.isOpened():
        raise RuntimeError(f"cannot open original video: {args.original}")
    if not blurred_capture.isOpened():
        raise RuntimeError(f"cannot open blurred video: {args.blurred}")

    reductions: list[float] = []
    original_scores: list[float] = []
    blurred_scores: list[float] = []
    frames_scanned = 0
    detections = 0
    try:
        while frames_scanned < args.max_frames:
            ok_original, original = original_capture.read()
            ok_blurred, blurred = blurred_capture.read()
            if not ok_original or not ok_blurred:
                break
            height, width = original.shape[:2]
            for detection in detector.detect(original):
                if detection.kind != "face":
                    continue
                box = detection.clipped(width, height, settings.face_blur_padding)
                if not box.is_valid:
                    continue
                original_roi = original[box.y1 : box.y2, box.x1 : box.x2]
                blurred_roi = blurred[box.y1 : box.y2, box.x1 : box.x2]
                if original_roi.size == 0 or blurred_roi.size == 0:
                    continue
                original_score = sharpness(original_roi)
                blurred_score = sharpness(blurred_roi)
                if original_score <= 0:
                    continue
                original_scores.append(original_score)
                blurred_scores.append(blurred_score)
                reductions.append((original_score - blurred_score) / original_score)
                detections += 1
            frames_scanned += 1
    finally:
        original_capture.release()
        blurred_capture.release()

    report = {
        "original": str(args.original),
        "blurred": str(args.blurred),
        "frames_scanned": frames_scanned,
        "face_detections": detections,
        "average_original_sharpness": sum(original_scores) / len(original_scores)
        if original_scores
        else 0.0,
        "average_blurred_sharpness": sum(blurred_scores) / len(blurred_scores)
        if blurred_scores
        else 0.0,
        "average_sharpness_reduction": sum(reductions) / len(reductions) if reductions else 0.0,
        "min_sharpness_reduction": min(reductions) if reductions else 0.0,
        "max_sharpness_reduction": max(reductions) if reductions else 0.0,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
