import os
import tempfile
import time
import unittest
from pathlib import Path

from backend.app.services.cleanup_service import CleanupService


class CleanupServiceTests(unittest.TestCase):
    def test_removes_expired_children_but_keeps_gitkeep(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            expired_file = root / "old.txt"
            expired_dir = root / "old_dir"
            fresh_file = root / "fresh.txt"
            gitkeep = root / ".gitkeep"
            expired_file.write_text("old", encoding="utf-8")
            expired_dir.mkdir()
            (expired_dir / "nested.txt").write_text("nested", encoding="utf-8")
            fresh_file.write_text("fresh", encoding="utf-8")
            gitkeep.write_text("", encoding="utf-8")

            now = time.time()
            old_time = now - 120
            os.utime(expired_file, (old_time, old_time))
            os.utime(expired_dir, (old_time, old_time))
            os.utime(fresh_file, (now, now))
            os.utime(gitkeep, (old_time, old_time))

            removed = CleanupService(ttl_seconds=60).cleanup_expired_children(root, now)

            self.assertEqual({path.name for path in removed}, {"old.txt", "old_dir"})
            self.assertFalse(expired_file.exists())
            self.assertFalse(expired_dir.exists())
            self.assertTrue(fresh_file.exists())
            self.assertTrue(gitkeep.exists())


if __name__ == "__main__":
    unittest.main()
