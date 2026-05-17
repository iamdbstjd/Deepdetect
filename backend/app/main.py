from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api.routes_jobs import build_jobs_router
from backend.app.api.routes_realtime import build_realtime_router
from backend.app.core.config import get_settings
from backend.app.core.paths import ensure_directories, jobs_dir, outputs_dir
from backend.app.services.job_service import JobService
from backend.app.services.queue_service import SimpleJobQueue
from backend.app.services.realtime_processor import RealtimeFrameProcessor
from backend.app.services.realtime_service import RealtimeSessionService
from backend.app.services.video_service import VideoJobProcessor
from backend.app.vision.character_overlay import CharacterAssetStore
from backend.app.vision.face_identity import build_face_matcher
from backend.app.vision.renderer import PrivacyRenderer
from backend.app.vision.tracker import DetectionTracker
from backend.app.vision.video_pipeline import BlurVideoPipeline
from backend.app.vision.yolo_detector import build_detector


settings = get_settings()
ensure_directories(settings)

job_service = JobService(jobs_dir(settings))
detector = build_detector(settings)
renderer = PrivacyRenderer(
    face_padding=settings.face_blur_padding,
    plate_padding=settings.plate_blur_padding,
)
face_matcher = build_face_matcher(settings, reference_detector=detector)
character_store = CharacterAssetStore(settings.project_root / "assets" / "characters")
tracker = (
    DetectionTracker(
        iou_threshold=settings.tracker_iou_threshold,
        smoothing_alpha=settings.tracker_smoothing_alpha,
        max_missing=settings.tracker_max_missing,
    )
    if settings.tracker_enabled
    else None
)


def build_tracker() -> DetectionTracker | None:
    if not settings.tracker_enabled:
        return None
    return DetectionTracker(
        iou_threshold=settings.tracker_iou_threshold,
        smoothing_alpha=settings.tracker_smoothing_alpha,
        max_missing=settings.tracker_max_missing,
    )


pipeline = BlurVideoPipeline(
    detector,
    renderer,
    face_matcher=face_matcher,
    character_store=character_store,
    tracker=tracker,
)
processor = VideoJobProcessor(outputs_dir(settings), pipeline=pipeline)
job_queue = SimpleJobQueue(job_service, processor)
realtime_service = RealtimeSessionService()
realtime_frame_processor = RealtimeFrameProcessor(
    detector=detector,
    renderer=renderer,
    face_matcher=face_matcher,
    character_store=character_store,
    tracker_factory=build_tracker,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    job_queue.start()
    try:
        yield
    finally:
        job_queue.stop()


app = FastAPI(
    title="Embed Privacy Video Filter",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(build_jobs_router(job_service, job_queue, settings))
app.include_router(build_realtime_router(realtime_service, realtime_frame_processor, settings))


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
