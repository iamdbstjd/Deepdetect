from __future__ import annotations

import json
from pathlib import Path
import shutil
import time
from typing import Callable

from backend.app.schemas.jobs import JobRecord
from backend.app.vision.video_pipeline import BlurVideoPipeline, VideoPipelineCancelled


class JobCancelled(RuntimeError):
    pass


ProgressCallback = Callable[[int, str], None]
CancelledCallback = Callable[[], bool]


class VideoJobProcessor:
    def __init__(self, outputs_dir: Path, pipeline: BlurVideoPipeline | None = None):
        self.outputs_dir = outputs_dir
        self.pipeline = pipeline
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

    def process(
        self,
        record: JobRecord,
        on_progress: ProgressCallback,
        is_cancelled: CancelledCallback,
    ) -> Path:
        source = Path(record.video_path)
        if not source.exists():
            raise FileNotFoundError(f"video file not found: {source}")

        output_dir = self.outputs_dir / record.job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        result_path = output_dir / "result.mp4"

        if self.pipeline:
            return self._process_with_pipeline(
                record,
                source,
                result_path,
                output_dir,
                on_progress,
                is_cancelled,
            )

        return self._process_placeholder(
            record,
            source,
            result_path,
            output_dir,
            on_progress,
            is_cancelled,
        )

    def _process_with_pipeline(
        self,
        record: JobRecord,
        source: Path,
        result_path: Path,
        output_dir: Path,
        on_progress: ProgressCallback,
        is_cancelled: CancelledCallback,
    ) -> Path:
        on_progress(5, "Starting blur pipeline")
        try:
            stats = self.pipeline.process_video(
                source,
                result_path,
                reference_image_path=(
                    Path(record.reference_image_path) if record.reference_image_path else None
                ),
                reference_image_paths=[
                    Path(path) for path in (record.reference_image_paths or [])
                ],
                mode=record.mode,
                character_id=record.character_id,
                on_progress=on_progress,
                is_cancelled=is_cancelled,
            )
        except VideoPipelineCancelled as exc:
            result_path.unlink(missing_ok=True)
            raise JobCancelled(str(exc)) from exc
        except Exception:
            result_path.unlink(missing_ok=True)
            raise
        self._write_metadata(
            output_dir,
            {
                "job_id": record.job_id,
                "phase": "phase_2_blur_pipeline",
                "source": str(source),
                "result": str(result_path),
                "detector": type(self.pipeline.detector).__name__,
                "face_matcher": (
                    type(self.pipeline.face_matcher).__name__
                    if self.pipeline.face_matcher
                    else None
                ),
                "stats": stats,
            },
        )
        return result_path

    def _process_placeholder(
        self,
        record: JobRecord,
        source: Path,
        result_path: Path,
        output_dir: Path,
        on_progress: ProgressCallback,
        is_cancelled: CancelledCallback,
    ) -> Path:
        on_progress(10, "Preparing placeholder video result")
        self._raise_if_cancelled(is_cancelled)
        time.sleep(0.01)

        on_progress(50, "Copying uploaded video as Phase 1 dummy result")
        self._raise_if_cancelled(is_cancelled)
        shutil.copy2(source, result_path)

        self._write_metadata(
            output_dir,
            {
                "job_id": record.job_id,
                "phase": "phase_1_placeholder",
                "source": str(source),
                "result": str(result_path),
                "note": "YOLO blur processing is planned for Phase 2.",
            },
        )

        on_progress(100, "Dummy result ready")
        return result_path

    @staticmethod
    def _write_metadata(output_dir: Path, payload: dict[str, object]) -> None:
        sidecar = output_dir / "metadata.json"
        sidecar.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @staticmethod
    def _raise_if_cancelled(is_cancelled: CancelledCallback) -> None:
        if is_cancelled():
            raise JobCancelled("job was cancelled")
