from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
import time
from typing import Any


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobRecord:
    job_id: str
    status: JobStatus
    mode: str
    character_id: str | None
    video_path: str
    reference_image_path: str
    result_path: str | None = None
    emoji_image_path: str | None = None
    progress: int = 0
    message: str = ""
    error: str | None = None
    created_at: float = 0.0
    updated_at: float = 0.0

    def __post_init__(self) -> None:
        now = time.time()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now
        if not isinstance(self.status, JobStatus):
            self.status = JobStatus(self.status)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data

    def to_public_dict(self) -> dict[str, Any]:
        result_url = None
        if self.status == JobStatus.DONE and self.result_path:
            result_url = f"/api/jobs/{self.job_id}/result"
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message,
            "error": self.error,
            "result_url": result_url,
            "status_url": f"/api/jobs/{self.job_id}",
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JobRecord":
        return cls(**data)

    @property
    def result_file(self) -> Path | None:
        return Path(self.result_path) if self.result_path else None