import importlib
import os
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np
from fastapi.testclient import TestClient


class ApiRealtimeTests(unittest.TestCase):
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

    def test_session_and_frame_processing(self) -> None:
        reference_bytes = self._image_bytes()
        frame_bytes = self._image_bytes()
        with TestClient(self.main.app) as client:
            session_response = client.post(
                "/api/realtime/sessions",
                files={"reference_image": ("face.jpg", reference_bytes, "image/jpeg")},
                data={"mode": "preserve"},
            )
            self.assertEqual(session_response.status_code, 200, session_response.text)
            session_id = session_response.json()["session_id"]

            frame_response = client.post(
                "/api/realtime/frame",
                files={"frame": ("frame.jpg", frame_bytes, "image/jpeg")},
                data={"session_id": session_id},
            )

        self.assertEqual(frame_response.status_code, 200, frame_response.text)
        self.assertEqual(frame_response.headers["content-type"], "image/jpeg")
        decoded = cv2.imdecode(
            np.frombuffer(frame_response.content, dtype=np.uint8),
            cv2.IMREAD_COLOR,
        )
        self.assertIsNotNone(decoded)

    def test_frame_requires_session_id(self) -> None:
        with TestClient(self.main.app) as client:
            response = client.post(
                "/api/realtime/frame",
                files={"frame": ("frame.jpg", self._image_bytes(), "image/jpeg")},
            )

        self.assertEqual(response.status_code, 400)

    def test_session_accepts_multiple_references_and_frame_metadata(self) -> None:
        reference_bytes = self._image_bytes()
        frame_bytes = self._image_bytes()
        with TestClient(self.main.app) as client:
            session_response = client.post(
                "/api/realtime/sessions",
                files=[
                    ("reference_images", ("face1.jpg", reference_bytes, "image/jpeg")),
                    ("reference_images", ("face2.jpg", reference_bytes, "image/jpeg")),
                ],
                data={"mode": "preserve"},
            )
            self.assertEqual(session_response.status_code, 200, session_response.text)
            self.assertEqual(session_response.json()["reference_count"], 2)

            frame_response = client.post(
                "/api/realtime/frame-meta",
                files={"frame": ("frame.jpg", frame_bytes, "image/jpeg")},
                data={"session_id": session_response.json()["session_id"]},
            )

        self.assertEqual(frame_response.status_code, 200, frame_response.text)
        payload = frame_response.json()
        self.assertTrue(payload["image"].startswith("data:image/jpeg;base64,"))
        self.assertEqual(payload["candidates"], [])

    def test_rejects_oversized_frame_upload(self) -> None:
        reference_bytes = self._image_bytes()
        oversized = b"x" * (self.main.settings.max_realtime_frame_bytes + 1)
        with TestClient(self.main.app) as client:
            session_response = client.post(
                "/api/realtime/sessions",
                files={"reference_image": ("face.jpg", reference_bytes, "image/jpeg")},
                data={"mode": "preserve"},
            )
            self.assertEqual(session_response.status_code, 200, session_response.text)
            response = client.post(
                "/api/realtime/frame",
                files={"frame": ("frame.jpg", oversized, "image/jpeg")},
                data={"session_id": session_response.json()["session_id"]},
            )

        self.assertEqual(response.status_code, 413)

    def _image_bytes(self) -> bytes:
        path = Path(self.tmp.name) / "image.jpg"
        image = np.zeros((64, 64, 3), dtype=np.uint8)
        image[16:48, 16:48] = (255, 255, 255)
        cv2.imwrite(str(path), image)
        return path.read_bytes()


if __name__ == "__main__":
    unittest.main()
