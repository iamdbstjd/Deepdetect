import tempfile
import unittest
from pathlib import Path

from backend.app.schemas.jobs import JobStatus
from backend.app.services.job_service import JobService
from backend.app.services.video_service import VideoJobProcessor


class JobServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.jobs = JobService(self.root / "jobs")
        self.video = self.root / "input.mp4"
        self.reference = self.root / "reference.jpg"
        self.video.write_bytes(b"fake video")
        self.reference.write_bytes(b"fake image")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_creates_and_updates_job(self) -> None:
        record = self.jobs.create_job(
            self.video, self.reference, "preserve", None, job_id="job_test"
        )
        self.assertEqual(record.status, JobStatus.QUEUED)

        self.jobs.mark_processing("job_test")
        processing = self.jobs.get("job_test")
        self.assertEqual(processing.status, JobStatus.PROCESSING)

        result = self.root / "result.mp4"
        result.write_bytes(b"result")
        self.jobs.mark_done("job_test", result)
        done = self.jobs.get("job_test")
        self.assertEqual(done.status, JobStatus.DONE)
        self.assertEqual(done.progress, 100)

    def test_video_processor_creates_placeholder_result(self) -> None:
        record = self.jobs.create_job(
            self.video, self.reference, "preserve", None, job_id="job_video"
        )
        processor = VideoJobProcessor(self.root / "outputs")
        events: list[tuple[int, str]] = []

        result = processor.process(
            record,
            on_progress=lambda progress, message: events.append((progress, message)),
            is_cancelled=lambda: False,
        )

        self.assertTrue(result.exists())
        self.assertEqual(result.read_bytes(), b"fake video")
        self.assertEqual(events[-1][0], 100)


if __name__ == "__main__":
    unittest.main()

