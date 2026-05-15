from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import threading
import time
import uuid

from backend.app.services.realtime_processor import RealtimeRuntime


@dataclass
class RealtimeSession:
    session_id: str
    reference_image_path: str
    mode: str
    character_id: str | None
    created_at: float
    updated_at: float
    runtime: RealtimeRuntime | None = None

    def to_public_dict(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "status": "ready",
            "mode": self.mode,
            "character_id": self.character_id,
            "websocket_url": f"/api/realtime/sessions/{self.session_id}/ws",
        }


class RealtimeSessionService:
    def __init__(self, ttl_seconds: int = 60 * 10):
        self.ttl_seconds = ttl_seconds
        self._lock = threading.RLock()
        self._sessions: dict[str, RealtimeSession] = {}

    def create_session(
        self,
        reference_image_path: Path,
        mode: str,
        character_id: str | None,
        runtime: RealtimeRuntime | None = None,
        session_id: str | None = None,
    ) -> RealtimeSession:
        now = time.time()
        session = RealtimeSession(
            session_id=session_id or uuid.uuid4().hex,
            reference_image_path=str(reference_image_path),
            mode=mode,
            character_id=character_id,
            created_at=now,
            updated_at=now,
            runtime=runtime,
        )
        with self._lock:
            self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> RealtimeSession | None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.updated_at = time.time()
            return session

    def cleanup_expired(self, now: float | None = None) -> list[str]:
        now = now or time.time()
        expired: list[str] = []
        with self._lock:
            for session_id, session in list(self._sessions.items()):
                if now - session.updated_at >= self.ttl_seconds:
                    expired.append(session_id)
                    del self._sessions[session_id]
        return expired
