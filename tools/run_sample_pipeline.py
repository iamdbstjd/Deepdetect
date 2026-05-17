from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from pathlib import Path
from typing import Any

import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")

from backend.app.core.config import Settings, get_settings  # noqa: E402
from backend.app.vision.character_overlay import CharacterAssetStore  # noqa: E402
from backend.app.vision.face_identity import build_face_matcher  # noqa: E402
from backend.app.vision.renderer import PrivacyRenderer  # noqa: E402
from backend.app.vision.tracker import DetectionTracker  # noqa: E402
from backend.app.vision.video_pipeline import BlurVideoPipeline  # noqa: E402
from backend.app.vision.yolo_detector import build_detector  # noqa: E402


def build_pipeline(settings: Settings) -> BlurVideoPipeline:
    detector = build_detector(settings)
    renderer = PrivacyRenderer(
        face_padding=settings.face_blur_padding,
        plate_padding=settings.plate_blur_padding,
    )
    tracker = (
        DetectionTracker(
            iou_threshold=settings.tracker_iou_threshold,
            smoothing_alpha=settings.tracker_smoothing_alpha,
            max_missing=settings.tracker_max_missing,
        )
        if settings.tracker_enabled
        else None
    )
    return BlurVideoPipeline(
        detector=detector,
        renderer=renderer,
        face_matcher=build_face_matcher(settings),
        character_store=CharacterAssetStore(settings.project_root / "assets" / "characters"),
        tracker=tracker,
    )


def summarize_scores(scores: list[float], threshold: float) -> dict[str, Any]:
    if not scores:
        return {
            "sample_count": 0,
            "threshold": threshold,
            "matches_at_threshold": 0,
        }
    ordered = sorted(scores)
    return {
        "sample_count": len(scores),
        "threshold": threshold,
        "matches_at_threshold": sum(1 for score in scores if score >= threshold),
        "min": ordered[0],
        "p10": ordered[max(0, int((len(ordered) - 1) * 0.10))],
        "median": statistics.median(ordered),
        "mean": statistics.fmean(ordered),
        "p90": ordered[min(len(ordered) - 1, int((len(ordered) - 1) * 0.90))],
        "max": ordered[-1],
    }


def collect_identity_scores(
    pipeline: BlurVideoPipeline,
    reference: Path | None,
    threshold: float,
    video: Path,
    max_frames: int,
) -> dict[str, Any]:
    if reference is None:
        return {"sample_count": 0, "threshold": threshold, "skipped": "no reference image"}
    prepared = pipeline.face_matcher.prepare(reference) if pipeline.face_matcher else None
    if prepared is None:
        return {"sample_count": 0, "threshold": threshold, "skipped": "face matcher disabled"}

    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise RuntimeError(f"cannot open video for score diagnostics: {video}")
    scores: list[float] = []
    frames_scanned = 0
    face_detections = 0
    try:
        while frames_scanned < max_frames:
            ok, frame = capture.read()
            if not ok:
                break
            detections = pipeline.detector.detect(frame)
            for detection in detections:
                if detection.kind != "face" or not detection.is_valid:
                    continue
                face_detections += 1
                scores.append(prepared.match_score(frame, detection))
            frames_scanned += 1
    finally:
        capture.release()

    summary = summarize_scores(scores, threshold)
    summary["frames_scanned"] = frames_scanned
    summary["face_detections"] = face_detections
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the privacy video pipeline on a sample clip.")
    parser.add_argument("--video", type=Path, default=Path("samples/videos/akiyo_short.mp4"))
    parser.add_argument("--reference", type=Path, default=Path("samples/references/akiyo_reference.jpg"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--mode", choices=("blur", "preserve", "character"), default="preserve")
    parser.add_argument("--character-id", default="default_emoji")
    parser.add_argument("--score-frames", type=int, default=30)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.video.exists():
        raise FileNotFoundError(f"sample video does not exist: {args.video}")
    reference = None if args.mode == "blur" else args.reference
    if reference is not None and not reference.exists():
        raise FileNotFoundError(f"reference image does not exist: {reference}")

    settings = get_settings()
    pipeline = build_pipeline(settings)
    progress_messages: list[dict[str, Any]] = []

    def on_progress(progress: int, message: str) -> None:
        payload = {"progress": progress, "message": message}
        progress_messages.append(payload)
        print(f"{progress:3d}% {message}")

    started = time.perf_counter()
    score_diagnostics = collect_identity_scores(
        pipeline=pipeline,
        reference=reference,
        threshold=settings.face_match_threshold,
        video=args.video,
        max_frames=args.score_frames,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    stats = pipeline.process_video(
        input_path=args.video,
        output_path=args.output,
        reference_image_path=reference,
        mode=args.mode,
        character_id=args.character_id,
        on_progress=on_progress,
        is_cancelled=lambda: False,
    )
    elapsed_seconds = time.perf_counter() - started
    report = {
        "mode": args.mode,
        "video": str(args.video),
        "reference": str(reference) if reference else None,
        "output": str(args.output),
        "detector": type(pipeline.detector).__name__,
        "face_matcher": type(pipeline.face_matcher).__name__ if pipeline.face_matcher else None,
        "tracker_enabled": pipeline.tracker is not None,
        "settings": {
            "detector_confidence": settings.detector_confidence,
            "face_match_threshold": settings.face_match_threshold,
            "face_blur_padding": settings.face_blur_padding,
            "plate_blur_padding": settings.plate_blur_padding,
            "tracker_iou_threshold": settings.tracker_iou_threshold,
            "tracker_smoothing_alpha": settings.tracker_smoothing_alpha,
            "tracker_max_missing": settings.tracker_max_missing,
        },
        "elapsed_seconds": elapsed_seconds,
        "effective_fps": stats["frames"] / elapsed_seconds if elapsed_seconds > 0 else 0.0,
        "stats": stats,
        "identity_score_diagnostics": score_diagnostics,
        "progress": progress_messages,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
