import importlib
import os
import tempfile
import time
import unittest
from pathlib import Path

import cv2
import numpy as np
from fastapi.testclient import TestClient


class ApiJobFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.storage = Path(self.tmp.name) / "storage"
        os.environ["EMBED_STORAGE_DIR"] = str(self.storage)
        os.environ["EMBED_DETECTOR_MODE"] = "noop"

        from backend.app.core.config import get_settings

        get_settings.cache_clear()
        import backend.app.main as main

        self.main = importlib.reload(main)

    def tearDown(self) -> None:
        self.main.job_queue.stop()
        self.tmp.cleanup()
        os.environ.pop("EMBED_STORAGE_DIR", None)
        os.environ.pop("EMBED_DETECTOR_MODE", None)

    def test_upload_status_and_result_download(self) -> None:
        video_path = self._make_video()
        with TestClient(self.main.app) as client:
            reference_bytes = self._make_reference_image()
            response = client.post(
                "/api/jobs/video",
                files={
                    "video": ("sample.mp4", video_path.read_bytes(), "video/mp4"),
                    "reference_image": ("face.jpg", reference_bytes, "image/jpeg"),
                },
                data={"mode": "preserve", "character_id": "default_mask"},
            )
            self.assertEqual(response.status_code, 200, response.text)
            payload = response.json()
            job_id = payload["job_id"]
            self.assertEqual(payload["status"], "queued")

            status = None
            for _ in range(40):
                status_response = client.get(f"/api/jobs/{job_id}")
                self.assertEqual(status_response.status_code, 200)
                status = status_response.json()
                if status["status"] == "done":
                    break
                time.sleep(0.05)

            self.assertIsNotNone(status)
            self.assertEqual(status["status"], "done", status)
            self.assertEqual(status["progress"], 100)

            result_response = client.get(f"/api/jobs/{job_id}/result")
            self.assertEqual(result_response.status_code, 200)
            self.assertGreater(len(result_response.content), 0)

    def test_failed_reference_upload_cleans_partial_video(self) -> None:
        video_path = self._make_video()
        with TestClient(self.main.app) as client:
            response = client.post(
                "/api/jobs/video",
                files={
                    "video": ("sample.mp4", video_path.read_bytes(), "video/mp4"),
                    "reference_image": ("face.exe", b"not an image", "image/jpeg"),
                },
                data={"mode": "preserve"},
            )

        self.assertEqual(response.status_code, 400)
        uploads_dir = self.storage / "uploads"
        remaining = [path for path in uploads_dir.iterdir() if path.name != ".gitkeep"]
        self.assertEqual(remaining, [])

    def test_result_download_rejects_path_outside_job_output_dir(self) -> None:
        outside = Path(self.tmp.name) / "outside.mp4"
        outside.write_bytes(b"outside")
        video = Path(self.tmp.name) / "input.mp4"
        reference = Path(self.tmp.name) / "reference.jpg"
        video.write_bytes(b"video")
        reference.write_bytes(b"reference")
        self.main.job_service.create_job(
            video,
            reference,
            "preserve",
            None,
            job_id="unsafe_job",
        )
        self.main.job_service.mark_done("unsafe_job", outside)

        with TestClient(self.main.app) as client:
            response = client.get("/api/jobs/unsafe_job/result")

        self.assertEqual(response.status_code, 404)

    def _make_video(self) -> Path:
        path = Path(self.tmp.name) / "sample.mp4"
        writer = cv2.VideoWriter(
            str(path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            5,
            (64, 64),
        )
        self.assertTrue(writer.isOpened())
        for _ in range(3):
            frame = np.zeros((64, 64, 3), dtype=np.uint8)
            frame[16:48, 16:48] = (255, 255, 255)
            writer.write(frame)
        writer.release()
        return path

    def _make_reference_image(self) -> bytes:
        path = Path(self.tmp.name) / "face.jpg"
        image = np.zeros((64, 64, 3), dtype=np.uint8)
        image[16:48, 16:48] = (255, 255, 255)
        cv2.imwrite(str(path), image)
        return path.read_bytes()


if __name__ == "__main__":
    unittest.main()
