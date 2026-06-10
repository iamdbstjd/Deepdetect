from __future__ import annotations

from pathlib import Path
import re
import shutil
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from backend.app.core.config import Settings
from backend.app.core.paths import job_output_dir, job_upload_dir, temp_dir
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
from backend.app.services.candidate_service import extract_video_face_candidates
from backend.app.services.queue_service import SimpleJobQueue
from backend.app.vision.detections import RegionDetector
from backend.app.vision.face_identity import FaceIdentityMatcher


_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]+$")


def build_jobs_router(
    job_service: JobService,
    job_queue: SimpleJobQueue,
    settings: Settings,
    detector: RegionDetector,
    face_matcher: FaceIdentityMatcher | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/jobs", tags=["jobs"])

    @router.post("/video")
    async def create_video_job(
        video: UploadFile = File(...),
        reference_image: UploadFile | None = File(None),
        reference_images: list[UploadFile] | None = File(None),
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
            reference_paths = await _store_reference_uploads(
                reference_image,
                reference_images,
                upload_dir,
                settings,
            )
            record = job_service.create_job(
                video_path=video_path,
                reference_image_path=reference_paths[0] if reference_paths else None,
                reference_image_paths=reference_paths,
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

    @router.post("/video/candidates")
    async def create_video_candidates(video: UploadFile = File(...)) -> dict[str, object]:
        analysis_id = uuid.uuid4().hex
        analysis_dir = _candidate_analysis_dir(analysis_id, settings)
        try:
            analysis_dir.mkdir(parents=True, exist_ok=True)
            video_path = await _store_upload(video, analysis_dir, "video", settings)
            candidate_dir = analysis_dir / "faces"
            candidates = extract_video_face_candidates(
                video_path,
                detector,
                candidate_dir,
                max_candidates=settings.candidate_max_faces,
                duplicate_identity_threshold=settings.candidate_identity_threshold,
                face_matcher=face_matcher,
            )
            return {
                "analysis_id": analysis_id,
                "candidates": [
                    {
                        "candidate_id": candidate.candidate_id,
                        "image_url": (
                            f"/api/jobs/video/candidates/{analysis_id}/"
                            f"{candidate.candidate_id}"
                        ),
                        "frame_index": candidate.frame_index,
                        "confidence": round(float(candidate.confidence), 4),
                    }
                    for candidate in candidates
                ],
            }
        except (UploadValidationError, ValueError) as exc:
            if analysis_dir.exists():
                shutil.rmtree(analysis_dir, ignore_errors=True)
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/video/candidates/{analysis_id}/{candidate_id}")
    def get_video_candidate(analysis_id: str, candidate_id: str) -> FileResponse:
        image_path = _candidate_image_path(analysis_id, candidate_id, settings)
        if not image_path or not image_path.exists():
            raise HTTPException(status_code=404, detail="candidate not found")
        return FileResponse(path=image_path, media_type="image/jpeg")

    @router.post("/video/from-candidates")
    async def create_video_job_from_candidates(
        analysis_id: str = Form(...),
        selected_candidate_ids: list[str] | None = Form(None),
        reference_images: list[UploadFile] | None = File(None),
        mode: str = Form("preserve"),
        character_id: str | None = Form(None),
    ) -> dict[str, object]:
        upload_dir: Path | None = None
        try:
            parsed_mode = parse_processing_mode(mode)
            analysis_dir = _candidate_analysis_dir(analysis_id, settings)
            if not analysis_dir.exists():
                raise ValueError("candidate analysis not found")
            source_video = _candidate_video_path(analysis_dir)
            if not source_video:
                raise ValueError("candidate analysis video not found")

            job_id = uuid.uuid4().hex
            upload_dir = job_upload_dir(job_id, settings)
            upload_dir.mkdir(parents=True, exist_ok=True)
            video_path = upload_dir / source_video.name
            shutil.copy2(source_video, video_path)

            reference_paths: list[Path] = []
            for index, candidate_id in enumerate(_unique_ids(selected_candidate_ids or [])):
                candidate_path = _candidate_image_path(analysis_id, candidate_id, settings)
                if not candidate_path or not candidate_path.exists():
                    raise ValueError(f"candidate not found: {candidate_id}")
                destination = upload_dir / f"candidate_{index + 1:02d}_{candidate_path.name}"
                shutil.copy2(candidate_path, destination)
                reference_paths.append(destination)
            reference_paths.extend(
                await _store_reference_uploads(None, reference_images, upload_dir, settings)
            )

            record = job_service.create_job(
                video_path=video_path,
                reference_image_path=reference_paths[0] if reference_paths else None,
                reference_image_paths=reference_paths,
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
    destination_prefix: str | None = None,
) -> Path:
    metadata = validate_upload_metadata(
        upload.filename or "",
        upload.content_type,
        kind,
        settings,
    )
    prefix = safe_filename(destination_prefix or kind)
    destination = directory / f"{prefix}_{safe_filename(metadata.filename)}"
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


async def _store_reference_uploads(
    reference_image: UploadFile | None,
    reference_images: list[UploadFile] | None,
    directory: Path,
    settings: Settings,
) -> list[Path]:
    uploads: list[UploadFile] = []
    if reference_image and reference_image.filename:
        uploads.append(reference_image)
    uploads.extend(upload for upload in reference_images or [] if upload.filename)
    paths: list[Path] = []
    for index, upload in enumerate(uploads):
        paths.append(
            await _store_upload(
                upload,
                directory,
                "image",
                settings,
                destination_prefix=f"image_{index + 1:02d}",
            )
        )
    return paths


def _candidate_root(settings: Settings) -> Path:
    return temp_dir(settings) / "video-candidates"


def _candidate_analysis_dir(analysis_id: str, settings: Settings) -> Path:
    if not _SAFE_ID.fullmatch(analysis_id):
        raise ValueError("invalid candidate analysis id")
    return _candidate_root(settings) / analysis_id


def _candidate_image_path(
    analysis_id: str,
    candidate_id: str,
    settings: Settings,
) -> Path | None:
    if not _SAFE_ID.fullmatch(candidate_id):
        return None
    try:
        analysis_dir = _candidate_analysis_dir(analysis_id, settings)
        candidate_path = (analysis_dir / "faces" / f"{candidate_id}.jpg").resolve()
        faces_dir = (analysis_dir / "faces").resolve()
    except (OSError, ValueError):
        return None
    if not candidate_path.is_relative_to(faces_dir):
        return None
    return candidate_path


def _candidate_video_path(analysis_dir: Path) -> Path | None:
    videos = sorted(path for path in analysis_dir.glob("video_*") if path.is_file())
    return videos[0] if videos else None


def _unique_ids(values: list[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for value in values:
        candidate_id = value.strip()
        if not candidate_id or candidate_id in seen:
            continue
        seen.add(candidate_id)
        unique.append(candidate_id)
    return unique
