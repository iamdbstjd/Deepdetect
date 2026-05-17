from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
import os
from pathlib import Path


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    project_root: Path
    storage_root: Path
    max_video_bytes: int = 512 * 1024 * 1024
    max_image_bytes: int = 10 * 1024 * 1024
    result_ttl_seconds: int = 24 * 60 * 60
    cleanup_interval_seconds: int = 60
    worker_poll_seconds: float = 0.2
    detector_mode: str = "auto"
    yolo_face_model_path: Path | None = None
    yolo_plate_model_path: Path | None = None
    detector_confidence: float = 0.35
    face_blur_padding: float = 0.18
    plate_blur_padding: float = 0.12
    face_matcher_mode: str = "arcface"
    face_match_model_path: Path | None = None
    face_match_threshold: float = 0.35
    tracker_enabled: bool = True
    tracker_iou_threshold: float = 0.3
    tracker_smoothing_alpha: float = 0.55
    tracker_max_missing: int = 2
    allowed_video_exts: tuple[str, ...] = field(
        default_factory=lambda: ("mp4", "mov", "avi", "mkv")
    )
    allowed_image_exts: tuple[str, ...] = field(
        default_factory=lambda: ("jpg", "jpeg", "png", "webp")
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[3]
    storage_root = Path(os.getenv("EMBED_STORAGE_DIR", project_root / "storage"))
    face_model = Path(
        os.getenv("EMBED_YOLO_FACE_MODEL", project_root / "models" / "yolo" / "face_detector.pt")
    )
    plate_model = Path(
        os.getenv(
            "EMBED_YOLO_PLATE_MODEL",
            project_root / "models" / "plate" / "license_plate_detector.pt",
        )
    )
    return Settings(
        project_root=project_root,
        storage_root=storage_root,
        max_video_bytes=_int_env("EMBED_MAX_VIDEO_BYTES", 512 * 1024 * 1024),
        max_image_bytes=_int_env("EMBED_MAX_IMAGE_BYTES", 10 * 1024 * 1024),
        result_ttl_seconds=_int_env("EMBED_RESULT_TTL_SECONDS", 24 * 60 * 60),
        cleanup_interval_seconds=_int_env("EMBED_CLEANUP_INTERVAL_SECONDS", 60),
        detector_mode=os.getenv("EMBED_DETECTOR_MODE", "auto"),
        yolo_face_model_path=face_model,
        yolo_plate_model_path=plate_model,
        detector_confidence=_float_env("EMBED_DETECTOR_CONFIDENCE", 0.35),
        face_blur_padding=_float_env("EMBED_FACE_BLUR_PADDING", 0.18),
        plate_blur_padding=_float_env("EMBED_PLATE_BLUR_PADDING", 0.12),
        face_matcher_mode=os.getenv("EMBED_FACE_MATCHER_MODE", "arcface"),
        face_match_model_path=Path(
            os.getenv(
                "EMBED_FACE_MATCH_MODEL",
                project_root / "models" / "face" / "w600k_r50.onnx",
            )
        ),
        face_match_threshold=_float_env("EMBED_FACE_MATCH_THRESHOLD", 0.35),
        tracker_enabled=_bool_env("EMBED_TRACKER_ENABLED", True),
        tracker_iou_threshold=_float_env("EMBED_TRACKER_IOU_THRESHOLD", 0.3),
        tracker_smoothing_alpha=_float_env("EMBED_TRACKER_SMOOTHING_ALPHA", 0.55),
        tracker_max_missing=_int_env("EMBED_TRACKER_MAX_MISSING", 2),
    )
