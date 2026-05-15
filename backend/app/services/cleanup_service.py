from __future__ import annotations

from pathlib import Path
import shutil
import time


class CleanupService:
    def __init__(self, ttl_seconds: int):
        self.ttl_seconds = ttl_seconds

    def cleanup_expired_children(self, directory: Path, now: float | None = None) -> list[Path]:
        now = now or time.time()
        removed: list[Path] = []
        if not directory.exists():
            return removed
        for child in directory.iterdir():
            if child.name == ".gitkeep":
                continue
            try:
                age = now - child.stat().st_mtime
            except OSError:
                continue
            if age < self.ttl_seconds:
                continue
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)
            removed.append(child)
        return removed

