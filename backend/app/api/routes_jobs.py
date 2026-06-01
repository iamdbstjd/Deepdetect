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

# 라우터 생성, 필요 서비스 연결
def build_jobs_router(
    job_service: JobService,    # 비즈니스 로직
    job_queue: SimpleJobQueue,  # 작업 대기열 관리
    settings: Settings,         # 설정값 접근
) -> APIRouter:
    router = APIRouter(prefix="/api/jobs", tags=["jobs"])

    # 비디오 작업 생성, 비디오와 이미지 업로드 -> 새로운 작업 등록
    @router.post("/video")
    async def create_video_job(
        video: UploadFile = File(...),
        reference_image: UploadFile = File(...),
        mode: str = Form("preserve"),          # 영상 처리 방식 (원본 or 이모지)
        character_id: str | None = Form(None), # 이모지 대체 모드일 때 (어떤 이모지 사용)
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

    # 작업 조회
    @router.get("/{job_id}")
    def get_job(job_id: str) -> dict[str, object]:
        try:
            return job_service.get(job_id).to_public_dict()
        except JobNotFoundError as exc:
            raise HTTPException(status_code=404, detail="job not found") from exc

    # 작업 취소
    @router.post("/{job_id}/cancel")
    def cancel_job(job_id: str) -> dict[str, object]:
        try:
            return job_service.cancel(job_id).to_public_dict()
        except JobNotFoundError as exc:
            raise HTTPException(status_code=404, detail="job not found") from exc
        except InvalidJobTransitionError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    # 결과 반환
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


# 경로 검증 -> 사용자가 요청한 결과 파일이 해당 작업 폴더에 있는지
def _is_job_result_path(path: Path, job_id: str, settings: Settings) -> bool:
    try:
        resolved_path = path.resolve()
        resolved_output_dir = job_output_dir(job_id, settings).resolve()
    except OSError:
        return False
    return resolved_path.is_relative_to(resolved_output_dir)


# 사용자가 업로드한 파일을 검증, 서버의 디스크에 안전하게 저장하는 역할
async def _store_upload(
    upload: UploadFile,  # 받은 파일(업로드 파일)
    directory: Path,     # 저장할 폴더 경로
    kind: str,           # video인지 image인지
    settings: Settings,  # 설정값
) -> Path:
    # 메타데이터
    metadata = validate_upload_metadata(
        upload.filename or "",  # 파일이름 없으면 빈 문자열
        upload.content_type,    # video 또는 image
        kind, 
        settings,
    )
    destination = directory / f"{kind}_{safe_filename(metadata.filename)}"
    total = 0
    try:
        with destination.open("wb") as handle:
            while True:
                chunk = await upload.read(1024 * 1024) # 1MB씩 읽음 (chunk의 단위)
                if not chunk:
                    break           # 읽을 게 없으면 break
                total += len(chunk) 
                # 파일 크기보다 읽은 크기가 많을 때
                if total > metadata.max_bytes:
                    raise UploadValidationError(
                        f"{kind} file exceeds limit: {total} > {metadata.max_bytes}"
                    )
                handle.write(chunk) # 정상이면 파일에 작성
        validate_upload_size(total, metadata.max_bytes) # 에러 없이 다 읽었으면 저장
    # 저장 도중 어떠한 에러라도 발생하면 싹 다 지움
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await upload.close() 
    return destination
