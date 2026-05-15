from __future__ import annotations

from pathlib import Path
import shutil
import uuid

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile, WebSocket

from backend.app.api.routes_jobs import _store_upload
from backend.app.core.config import Settings
from backend.app.core.paths import temp_dir
from backend.app.core.security import UploadValidationError
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
        reference_image: UploadFile = File(...),
        mode: str = Form("preserve"),
        character_id: str | None = Form(None),
    ) -> dict[str, object]:
        session_dir: Path | None = None
        try:
            parsed_mode = parse_processing_mode(mode)
            session_id = uuid.uuid4().hex
            session_dir = temp_dir(settings) / "realtime" / session_id
            session_dir.mkdir(parents=True, exist_ok=True)
            reference_path = await _store_upload(
                reference_image, session_dir, "image", settings
            )
            runtime = frame_processor.create_runtime(
                reference_image_path=reference_path,
                mode=parsed_mode.value,
                character_id=character_id,
            )
            session = realtime_service.create_session(
                reference_image_path=reference_path,
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

    @router.websocket("/sessions/{session_id}/ws")
    async def realtime_websocket(websocket: WebSocket, session_id: str) -> None:
        session = realtime_service.get(session_id)
        if not session:
            await websocket.close(code=4404)
            return
        await websocket.accept()
        while True:
            frame = await websocket.receive_bytes()
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
        data = await frame.read()
        await frame.close()
        if not session.runtime:
            raise HTTPException(status_code=409, detail="session is not ready")
        try:
            rendered = frame_processor.process_frame(data, session.runtime)
        except RealtimeFrameError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return Response(content=rendered, media_type="image/jpeg")

    return router
