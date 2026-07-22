"""Remote operations — mission control, GCS, firmware, params, logs, diagnostics, streams (Sprint 11.8)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RemoteOperations:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def open_session(
        self,
        *,
        operator_id: str,
        aircraft_id: str = "",
        mode: str = "mission_control",
        location: str = "remote",
    ) -> dict[str, Any]:
        if not operator_id:
            raise ValidationError("operator_id required")
        rid = f"rmt_{uuid.uuid4().hex[:12]}"
        session = {
            "remote_session_id": rid,
            "operator_id": operator_id,
            "aircraft_id": aircraft_id,
            "mode": mode,
            "location": location,
            "status": "active",
            "channels": {"telemetry": False, "camera": False, "shell": False},
            "created_at": _now(),
        }
        self.store.remote_sessions.save(rid, session)
        return session

    def get_session(self, remote_session_id: str) -> dict[str, Any]:
        item = self.store.remote_sessions.get(remote_session_id)
        if item is None:
            raise NotFoundError("remote_session", remote_session_id)
        return item

    def remote_mission_control(self, remote_session_id: str, *, command: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        session = self.get_session(remote_session_id)
        return {"session": session["remote_session_id"], "command": command, "params": dict(params or {}), "accepted": True, "at": _now()}

    def remote_ground_station(self, remote_session_id: str) -> dict[str, Any]:
        session = self.get_session(remote_session_id)
        return {"type": "remote_gcs", "session_id": session["remote_session_id"], "aircraft_id": session.get("aircraft_id"), "panels": ["map", "telemetry", "mission", "alerts"]}

    def remote_firmware_upload(self, remote_session_id: str, *, firmware_id: str, version: str = "") -> dict[str, Any]:
        self.get_session(remote_session_id)
        job = {
            "job_id": f"rfw_{uuid.uuid4().hex[:10]}",
            "remote_session_id": remote_session_id,
            "firmware_id": firmware_id,
            "version": version,
            "status": "queued",
            "at": _now(),
        }
        self.store.remote_jobs.save(job["job_id"], job)
        return job

    def remote_parameter_edit(self, remote_session_id: str, *, parameters: dict[str, Any]) -> dict[str, Any]:
        self.get_session(remote_session_id)
        return {"remote_session_id": remote_session_id, "updated": dict(parameters), "count": len(parameters), "status": "applied", "at": _now()}

    def remote_mission_upload(self, remote_session_id: str, *, waypoints: list[dict[str, Any]], mission_name: str = "") -> dict[str, Any]:
        self.get_session(remote_session_id)
        mid = f"rmis_{uuid.uuid4().hex[:10]}"
        payload = {
            "upload_id": mid,
            "remote_session_id": remote_session_id,
            "mission_name": mission_name or "remote_mission",
            "waypoint_count": len(waypoints),
            "status": "uploaded",
            "at": _now(),
        }
        self.store.remote_jobs.save(mid, payload)
        return payload

    def remote_log_download(self, remote_session_id: str, *, log_id: str = "") -> dict[str, Any]:
        self.get_session(remote_session_id)
        return {
            "remote_session_id": remote_session_id,
            "log_id": log_id or f"log_{uuid.uuid4().hex[:8]}",
            "url": f"cloud://logs/{log_id or 'latest'}.bin",
            "status": "ready",
            "at": _now(),
        }

    def remote_diagnostics(self, remote_session_id: str) -> dict[str, Any]:
        session = self.get_session(remote_session_id)
        return {
            "remote_session_id": remote_session_id,
            "aircraft_id": session.get("aircraft_id"),
            "checks": {"link": "ok", "gps": "ok", "battery": "ok", "imu": "ok"},
            "health_score": 0.92,
            "at": _now(),
        }

    def remote_camera_stream(self, remote_session_id: str, *, enable: bool = True) -> dict[str, Any]:
        session = self.get_session(remote_session_id)
        session["channels"]["camera"] = enable
        self.store.remote_sessions.save(remote_session_id, session)
        return {"remote_session_id": remote_session_id, "camera_stream": enable, "url": f"wss://cloud/stream/{remote_session_id}" if enable else ""}

    def remote_telemetry(self, remote_session_id: str, *, enable: bool = True) -> dict[str, Any]:
        session = self.get_session(remote_session_id)
        session["channels"]["telemetry"] = enable
        self.store.remote_sessions.save(remote_session_id, session)
        return {"remote_session_id": remote_session_id, "telemetry": enable, "topics": ["attitude", "position", "battery", "mode"]}

    def remote_shell(self, remote_session_id: str, *, command: str) -> dict[str, Any]:
        self.get_session(remote_session_id)
        if not command:
            raise ValidationError("shell command required")
        return {"remote_session_id": remote_session_id, "command": command, "output": f"ok: {command}", "exit_code": 0, "at": _now()}

    def status(self) -> dict[str, Any]:
        return {
            "remote_operations": "1.0",
            "sessions": len(self.store.remote_sessions.list_all()),
            "jobs": len(self.store.remote_jobs.list_all()),
            "ready": True,
        }


remote_operations = RemoteOperations()
