import tempfile
import unittest
from pathlib import Path

from backend.app.core.config import Settings
from backend.app.core.security import (
    UploadValidationError,
    safe_filename,
    validate_upload_metadata,
    validate_upload_size,
)


class UploadValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.settings = Settings(project_root=root, storage_root=root / "storage")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_accepts_valid_video_metadata(self) -> None:
        result = validate_upload_metadata(
            "sample.mp4", "video/mp4", "video", self.settings
        )
        self.assertEqual(result.extension, "mp4")

    def test_rejects_bad_video_extension(self) -> None:
        with self.assertRaises(UploadValidationError):
            validate_upload_metadata("sample.exe", "video/mp4", "video", self.settings)

    def test_accepts_valid_image_metadata(self) -> None:
        result = validate_upload_metadata(
            "face.png", "image/png", "image", self.settings
        )
        self.assertEqual(result.extension, "png")

    def test_rejects_empty_upload_size(self) -> None:
        with self.assertRaises(UploadValidationError):
            validate_upload_size(0, 100)

    def test_sanitizes_filename(self) -> None:
        self.assertEqual(safe_filename("../my face!!.jpg"), "my_face_.jpg")


if __name__ == "__main__":
    unittest.main()

