from __future__ import annotations

from pathlib import Path
import shutil
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from backend.app.core.config import Settings
from backend.app.core.paths import job_output_dir, job_upload_dir
from backend.app.core.security import (
    UploadValidationError,
    safe_filename,
    validate_upload_metadata,
    validate_upload_size,
)
from backend.app.schemas.processing import parse_processing_mode
from backend.app.services.job_service import (
    InvalidJobTransitionError,
    JobNotFoundError,
    JobService,
)
from backend.app.services.queue_service import SimpleJobQueue


def build_jobs_router(
    job_service: JobService,
    job_queue: SimpleJobQueue,
    settings: Settings,
) -> APIRouter:
    router = APIRouter(prefix="/api/jobs", tags=["jobs"])

    @router.post("/video")
    async def create_video_job(
        video: UploadFile = File(...),
        reference_image: UploadFile = File(...),
        mode: str = Form("preserve"),
        character_id: str | None = Form(None),
    ) -> dict[str, object]:
        upload_dir: Path | None = None
        try:
            parsed_mode = parse_processing_mode(mode)
            job_id = uuid.uuid4().hex
            upload_dir = job_upload_dir(job_id, settings)
            upload_dir.mkdir(parents=True, exist_ok=True)
            video_path = await _store_upload(video, upload_dir, "video", settings)
            reference_path = await _store_upload(
                reference_image, upload_dir, "image", settings
            )
            record = job_service.create_job(
                video_path=video_path,
                reference_image_path=reference_path,
                mode=parsed_mode.value,
                character_id=character_id,
                job_id=job_id,
            )
            job_queue.submit(record.job_id)
            return record.to_public_dict()
        except (UploadValidationError, ValueError) as exc:
            if upload_dir and upload_dir.exists():
                shutil.rmtree(upload_dir, ignore_errors=True)
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/{job_id}")
    def get_job(job_id: str) -> dict[str, object]:
        try:
            return job_service.get(job_id).to_public_dict()
        except JobNotFoundError as exc:
            raise HTTPException(status_code=404, detail="job not found") from exc

    @router.post("/{job_id}/cancel")
    def cancel_job(job_id: str) -> dict[str, object]:
        try:
            return job_service.cancel(job_id).to_public_dict()
        except JobNotFoundError as exc:
            raise HTTPException(status_code=404, detail="job not found") from exc
        except InvalidJobTransitionError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.get("/{job_id}/result")
    def get_result(job_id: str) -> FileResponse:
        try:
            record = job_service.get(job_id)
        except JobNotFoundError as exc:
            raise HTTPException(status_code=404, detail="job not found") from exc
        result_file = record.result_file
        if not result_file or not _is_job_result_path(result_file, job_id, settings):
            raise HTTPException(status_code=404, detail="result not ready")
        if not result_file.exists():
            raise HTTPException(status_code=404, detail="result not ready")
        return FileResponse(path=result_file, filename=result_file.name)

    return router


def _is_job_result_path(path: Path, job_id: str, settings: Settings) -> bool:
    try:
        resolved_path = path.resolve()
        resolved_output_dir = job_output_dir(job_id, settings).resolve()
    except OSError:
        return False
    return resolved_path.is_relative_to(resolved_output_dir)


async def _store_upload(
    upload: UploadFile,
    directory: Path,
    kind: str,
    settings: Settings,
) -> Path:
    metadata = validate_upload_metadata(
        upload.filename or "",
        upload.content_type,
        kind,
        settings,
    )
    destination = directory / f"{kind}_{safe_filename(metadata.filename)}"
    total = 0
    try:
        with destination.open("wb") as handle:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > metadata.max_bytes:
                    raise UploadValidationError(
                        f"{kind} file exceeds limit: {total} > {metadata.max_bytes}"
                    )
                handle.write(chunk)
        validate_upload_size(total, metadata.max_bytes)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()
    return destination
