"""Ground control — dashboards, alerts, operator/emergency consoles (Sprint 11.7)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class GroundControl:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def open_session(self, *, operator_id: str, role: str = "operator") -> dict[str, Any]:
        sid = f"gnd_{uuid.uuid4().hex[:12]}"
        session = {
            "session_id": sid,
            "operator_id": operator_id,
            "role": role,
            "status": "active",
            "opened_at": _now(),
            "dashboards": ["mission", "live_map", "telemetry", "health"],
        }
        self.store.ground_sessions.save(sid, session)
        return session

    def mission_dashboard(self, *, ops_mission_id: str = "", fleet_ids: list[str] | None = None) -> dict[str, Any]:
        return {
            "type": "mission_dashboard",
            "ops_mission_id": ops_mission_id,
            "fleet_ids": list(fleet_ids or []),
            "widgets": ["status", "timeline", "alerts", "assignments"],
            "at": _now(),
        }

    def live_map(self, *, tracks: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        return {"type": "live_map", "tracks": list(tracks or []), "layers": ["aircraft", "waypoints", "geofence"], "at": _now()}

    def telemetry_dashboard(self, *, samples: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        samples = list(samples or [])
        latest = samples[-1] if samples else {}
        return {"type": "telemetry_dashboard", "latest": latest, "sample_count": len(samples), "at": _now()}

    def health_dashboard(self, *, aircraft: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        aircraft = list(aircraft or [])
        healthy = sum(1 for a in aircraft if a.get("maintenance_status") == "ok")
        return {"type": "health_dashboard", "aircraft_count": len(aircraft), "healthy": healthy, "at": _now()}

    def mission_status(self, ops_mission: dict[str, Any]) -> dict[str, Any]:
        return {
            "ops_mission_id": ops_mission.get("ops_mission_id"),
            "name": ops_mission.get("name"),
            "status": ops_mission.get("status"),
            "priority": ops_mission.get("priority"),
            "waypoint_count": len(ops_mission.get("waypoints") or []),
        }

    def raise_alert(self, *, severity: str, message: str, source: str = "system", ops_mission_id: str = "") -> dict[str, Any]:
        aid = f"alt_{uuid.uuid4().hex[:12]}"
        alert = {
            "alert_id": aid,
            "severity": severity,
            "message": message,
            "source": source,
            "ops_mission_id": ops_mission_id,
            "status": "open",
            "created_at": _now(),
        }
        self.store.mission_alerts.save(aid, alert)
        return alert

    def list_alerts(self, *, open_only: bool = False) -> list[dict[str, Any]]:
        items = self.store.mission_alerts.list_all()
        if open_only:
            return [a for a in items if a.get("status") == "open"]
        return items

    def operator_console(self, session_id: str) -> dict[str, Any]:
        session = self.store.ground_sessions.get(session_id)
        if session is None:
            raise NotFoundError("ground_session", session_id)
        return {"console": "operator", "session": session, "actions": ["arm", "disarm", "mode", "rtl", "land"]}

    def emergency_console(self, session_id: str) -> dict[str, Any]:
        session = self.store.ground_sessions.get(session_id)
        if session is None:
            raise NotFoundError("ground_session", session_id)
        return {
            "console": "emergency",
            "session": session,
            "actions": ["abort", "rtl", "land_now", "kill_switch_arm_confirm"],
            "policy": "engineering_assistance_only",
        }

    def status(self) -> dict[str, Any]:
        return {
            "ground_control": "1.0",
            "sessions": self.store.ground_sessions.count(),
            "alerts": self.store.mission_alerts.count(),
            "capabilities": [
                "ground_station",
                "mission_dashboard",
                "live_map",
                "telemetry_dashboard",
                "health_dashboard",
                "mission_status",
                "alert_manager",
                "operator_console",
                "emergency_console",
            ],
        }


ground_control = GroundControl()
