from __future__ import annotations

import base64
from pathlib import Path
import shutil
import uuid

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile, WebSocket

from backend.app.api.routes_jobs import _store_reference_uploads
from backend.app.core.config import Settings
from backend.app.core.paths import temp_dir
from backend.app.core.security import UploadValidationError, safe_filename
from backend.app.schemas.processing import parse_processing_mode
from backend.app.services.realtime_processor import RealtimeFrameError, RealtimeFrameProcessor
from backend.app.services.realtime_service import RealtimeSessionService
from backend.app.vision.face_identity import FaceIdentityError


def build_realtime_router(
    realtime_service: RealtimeSessionService,
    frame_processor: RealtimeFrameProcessor,
    settings: Settings,
) -> APIRouter:
    router = APIRouter(prefix="/api/realtime", tags=["realtime"])

    @router.post("/sessions")
    async def create_session(
        reference_image: UploadFile | None = File(None),
        reference_images: list[UploadFile] | None = File(None),
        mode: str = Form("preserve"),
        character_id: str | None = Form(None),
    ) -> dict[str, object]:
        session_dir: Path | None = None
        try:
            parsed_mode = parse_processing_mode(mode)
            session_id = uuid.uuid4().hex
            session_dir = temp_dir(settings) / "realtime" / session_id
            session_dir.mkdir(parents=True, exist_ok=True)
            reference_paths = await _store_reference_uploads(
                reference_image,
                reference_images,
                session_dir,
                settings,
            )
            runtime = frame_processor.create_runtime(
                reference_image_path=reference_paths[0] if reference_paths else None,
                reference_image_paths=reference_paths,
                mode=parsed_mode.value,
                character_id=character_id,
            )
            session = realtime_service.create_session(
                reference_image_path=reference_paths[0] if reference_paths else None,
                reference_image_paths=reference_paths,
                mode=parsed_mode.value,
                character_id=character_id,
                runtime=runtime,
                session_id=session_id,
            )
            return session.to_public_dict()
        except (FaceIdentityError, RealtimeFrameError, UploadValidationError, ValueError) as exc:
            if session_dir and session_dir.exists():
                shutil.rmtree(session_dir, ignore_errors=True)
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/sessions/{session_id}/allow-face")
    async def allow_realtime_face(
        session_id: str,
        candidate_id: str = Form(...),
    ) -> dict[str, object]:
        session = realtime_service.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="session not found")
        if not session.runtime:
            raise HTTPException(status_code=409, detail="session is not ready")
        safe_candidate_id = safe_filename(candidate_id)
        if not safe_candidate_id:
            raise HTTPException(status_code=400, detail="candidate_id is required")
        reference_path = (
            temp_dir(settings)
            / "realtime"
            / session_id
            / f"allowed_{safe_candidate_id}.jpg"
        )
        try:
            accepted = frame_processor.allow_pending_face(
                session.runtime,
                candidate_id,
                reference_path,
            )
        except (FaceIdentityError, RealtimeFrameError, OSError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if not accepted:
            raise HTTPException(status_code=404, detail="candidate not found")
        session.reference_image_paths = session.reference_image_paths or []
        session.reference_image_paths.append(str(reference_path))
        if not session.reference_image_path:
            session.reference_image_path = str(reference_path)
        return {"accepted": True, "reference_count": len(session.reference_image_paths)}

    @router.websocket("/sessions/{session_id}/ws")
    async def realtime_websocket(websocket: WebSocket, session_id: str) -> None:
        session = realtime_service.get(session_id)
        if not session:
            await websocket.close(code=4404)
            return
        await websocket.accept()
        while True:
            frame = await websocket.receive_bytes()
            if len(frame) > settings.max_realtime_frame_bytes:
                await websocket.close(code=1009)
                return
            if not session.runtime:
                await websocket.close(code=1011)
                return
            try:
                rendered = frame_processor.process_frame(frame, session.runtime)
            except RealtimeFrameError:
                await websocket.close(code=1003)
                return
            await websocket.send_bytes(rendered)

    @router.post("/frame")
    async def process_frame_fallback(
        frame: UploadFile = File(...),
        session_id: str | None = Form(None),
    ) -> Response:
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        session = realtime_service.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="session not found")
        data = await _read_realtime_frame(frame, settings)
        if not session.runtime:
            raise HTTPException(status_code=409, detail="session is not ready")
        try:
            rendered = frame_processor.process_frame(data, session.runtime)
        except RealtimeFrameError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return Response(content=rendered, media_type="image/jpeg")

    @router.post("/frame-meta")
    async def process_frame_with_metadata(
        frame: UploadFile = File(...),
        session_id: str | None = Form(None),
    ) -> dict[str, object]:
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        session = realtime_service.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="session not found")
        data = await _read_realtime_frame(frame, settings)
        if not session.runtime:
            raise HTTPException(status_code=409, detail="session is not ready")
        try:
            result = frame_processor.process_frame_with_metadata(data, session.runtime)
        except RealtimeFrameError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "image": _data_url(result.image),
            "candidates": [
                {
                    "candidate_id": candidate.candidate_id,
                    "track_id": candidate.track_id,
                    "image": _data_url(candidate.image_bytes),
                }
                for candidate in result.candidates
            ],
        }

    return router


async def _read_realtime_frame(upload: UploadFile, settings: Settings) -> bytes:
    total = 0
    chunks: list[bytes] = []
    try:
        while True:
            chunk = await upload.read(1024 * 256)
            if not chunk:
                break
            total += len(chunk)
            if total > settings.max_realtime_frame_bytes:
                raise HTTPException(status_code=413, detail="realtime frame is too large")
            chunks.append(chunk)
    finally:
        await upload.close()
    if total <= 0:
        raise HTTPException(status_code=400, detail="realtime frame is empty")
    return b"".join(chunks)


def _data_url(image: bytes) -> str:
    encoded = base64.b64encode(image).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"
