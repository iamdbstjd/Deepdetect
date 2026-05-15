from __future__ import annotations

from pathlib import Path

from .config import Settings, get_settings


def ensure_directories(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    for path in (
        uploads_dir(settings),
        outputs_dir(settings),
        temp_dir(settings),
        jobs_dir(settings),
    ):
        path.mkdir(parents=True, exist_ok=True)


def uploads_dir(settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    return settings.storage_root / "uploads"


def outputs_dir(settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    return settings.storage_root / "outputs"


def temp_dir(settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    return settings.storage_root / "temp"


def jobs_dir(settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    return settings.storage_root / "jobs"


def job_upload_dir(job_id: str, settings: Settings | None = None) -> Path:
    return uploads_dir(settings) / job_id


def job_output_dir(job_id: str, settings: Settings | None = None) -> Path:
    return outputs_dir(settings) / job_id

