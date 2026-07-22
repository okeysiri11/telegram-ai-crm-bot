from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError
from applications.drone_platform.shared.store import DroneStore, drone_store


class TelemetryService:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def start_session(self, *, uav_id: str, mission_id: str = "", metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        sid = f"tel_{uuid.uuid4().hex[:12]}"
        session = {
            "session_id": sid,
            "uav_id": uav_id,
            "mission_id": mission_id,
            "samples": [],
            "metadata": dict(metadata or {}),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "status": "active",
        }
        self.store.telemetry_sessions.save(sid, session)
        return session

    def record_sample(self, session_id: str, sample: dict[str, Any]) -> dict[str, Any]:
        session = self.store.telemetry_sessions.get(session_id)
        if session is None:
            raise NotFoundError("telemetry_session", session_id)
        entry = {**sample, "recorded_at": datetime.now(timezone.utc).isoformat()}
        session["samples"].append(entry)
        self.store.telemetry_sessions.save(session_id, session)
        return session

    def get_session(self, session_id: str) -> dict[str, Any]:
        session = self.store.telemetry_sessions.get(session_id)
        if session is None:
            raise NotFoundError("telemetry_session", session_id)
        return session

    def list_sessions(self) -> list[dict[str, Any]]:
        return self.store.telemetry_sessions.list_all()


telemetry_service = TelemetryService()
