from __future__ import annotations

import json
from pathlib import Path
import threading
import time
import uuid

from backend.app.schemas.jobs import JobRecord, JobStatus


class JobNotFoundError(KeyError):
    pass


class InvalidJobTransitionError(RuntimeError):
    pass


class JobService:
    def __init__(self, jobs_dir: Path):
        self.jobs_dir = jobs_dir
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._jobs: dict[str, JobRecord] = {}
        self._load_existing()

    def create_job(
        self,
        video_path: Path,
        reference_image_path: Path,
        mode: str,
        character_id: str | None,
        job_id: str | None = None,
    ) -> JobRecord:
        job_id = job_id or uuid.uuid4().hex
        record = JobRecord(
            job_id=job_id,
            status=JobStatus.QUEUED,
            mode=mode,
            character_id=character_id,
            video_path=str(video_path),
            reference_image_path=str(reference_image_path),
            progress=0,
            message="Queued",
        )
        with self._lock:
            self._jobs[job_id] = record
            self._persist(record)
        return record

    def get(self, job_id: str) -> JobRecord:
        with self._lock:
            try:
                return self._jobs[job_id]
            except KeyError as exc:
                raise JobNotFoundError(job_id) from exc

    def mark_processing(self, job_id: str, message: str = "Processing") -> JobRecord:
        return self.update(job_id, status=JobStatus.PROCESSING, progress=1, message=message)

    def mark_done(self, job_id: str, result_path: Path, message: str = "Done") -> JobRecord:
        return self.update(
            job_id,
            status=JobStatus.DONE,
            progress=100,
            result_path=str(result_path),
            message=message,
            error=None,
        )

    def mark_failed(self, job_id: str, error: str) -> JobRecord:
        return self.update(
            job_id,
            status=JobStatus.FAILED,
            message="Failed",
            error=error,
        )

    def cancel(self, job_id: str) -> JobRecord:
        record = self.get(job_id)
        if record.status in (JobStatus.DONE, JobStatus.FAILED):
            raise InvalidJobTransitionError(
                f"cannot cancel job {job_id} from {record.status.value}"
            )
        return self.update(
            job_id,
            status=JobStatus.CANCELLED,
            message="Cancelled",
        )

    def is_cancelled(self, job_id: str) -> bool:
        return self.get(job_id).status == JobStatus.CANCELLED

    def update(self, job_id: str, **changes: object) -> JobRecord:
        with self._lock:
            record = self.get(job_id)
            for key, value in changes.items():
                if key == "status" and not isinstance(value, JobStatus):
                    value = JobStatus(str(value))
                setattr(record, key, value)
            record.updated_at = time.time()
            self._persist(record)
            return record

    def _persist(self, record: JobRecord) -> None:
        path = self.jobs_dir / f"{record.job_id}.json"
        path.write_text(json.dumps(record.to_dict(), indent=2), encoding="utf-8")

    def _load_existing(self) -> None:
        for path in self.jobs_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                record = JobRecord.from_dict(data)
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                continue
            self._jobs[record.job_id] = record

