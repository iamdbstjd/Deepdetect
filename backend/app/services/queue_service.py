from __future__ import annotations

import queue
import threading

from backend.app.schemas.jobs import JobStatus
from backend.app.services.job_service import JobService
from backend.app.services.video_service import JobCancelled, VideoJobProcessor


class SimpleJobQueue:
    def __init__(self, job_service: JobService, processor: VideoJobProcessor):
        self.job_service = job_service
        self.processor = processor
        self._queue: queue.Queue[str] = queue.Queue()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="embed-job-worker", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def submit(self, job_id: str) -> None:
        self._queue.put(job_id)

    def process_one(self, job_id: str) -> None:
        record = self.job_service.get(job_id)
        if record.status == JobStatus.CANCELLED:
            return
        self.job_service.mark_processing(job_id)
        try:
            result_path = self.processor.process(
                record,
                on_progress=lambda progress, message: self.job_service.update(
                    job_id, progress=progress, message=message
                ),
                is_cancelled=lambda: self.job_service.is_cancelled(job_id),
            )
        except JobCancelled:
            self.job_service.cancel(job_id)
        except Exception as exc:  # noqa: BLE001 - job errors must be reported.
            self.job_service.mark_failed(job_id, str(exc))
        else:
            self.job_service.mark_done(job_id, result_path)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                job_id = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue
            try:
                self.process_one(job_id)
            finally:
                self._queue.task_done()

