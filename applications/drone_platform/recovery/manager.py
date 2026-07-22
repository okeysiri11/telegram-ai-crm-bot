"""Autonomous recovery — RTL, safe landing, resume, link recovery, sensor reconfig (Sprint 11.9)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


EMERGENCY_MODES = ("rtl", "land", "hold", "terminate", "brake")


class RecoveryManager:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def start(
        self,
        *,
        aircraft_id: str,
        reason: str,
        mode: str = "rtl",
        home: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not aircraft_id or not reason:
            raise ValidationError("aircraft_id and reason required")
        if mode not in EMERGENCY_MODES:
            raise ValidationError(f"mode must be one of {EMERGENCY_MODES}")
        rid = f"rcv_{uuid.uuid4().hex[:12]}"
        event = {
            "recovery_id": rid,
            "aircraft_id": aircraft_id,
            "reason": reason,
            "mode": mode,
            "home": dict(home or {}),
            "status": "active",
            "timeline": [{"event": "started", "mode": mode, "at": _now()}],
            "metadata": dict(metadata or {}),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.recovery_events.save(rid, event)
        return event

    def get(self, recovery_id: str) -> dict[str, Any]:
        item = self.store.recovery_events.get(recovery_id)
        if item is None:
            raise NotFoundError("recovery_event", recovery_id)
        return item

    def _append(self, event: dict[str, Any], name: str, **extra: Any) -> dict[str, Any]:
        event["timeline"].append({"event": name, **extra, "at": _now()})
        event["updated_at"] = _now()
        self.store.recovery_events.save(event["recovery_id"], event)
        return event

    def automatic_return(self, recovery_id: str) -> dict[str, Any]:
        event = self.get(recovery_id)
        event["mode"] = "rtl"
        event["status"] = "returning"
        return self._append(event, "automatic_return", mode="rtl")

    def safe_landing(self, recovery_id: str, *, site: dict[str, Any] | None = None) -> dict[str, Any]:
        event = self.get(recovery_id)
        event["mode"] = "land"
        event["landing_site"] = dict(site or event.get("home") or {})
        event["status"] = "landing"
        return self._append(event, "safe_landing", site=event["landing_site"])

    def mission_resume(self, recovery_id: str, *, waypoint_index: int = 0) -> dict[str, Any]:
        event = self.get(recovery_id)
        event["status"] = "resumed"
        event["resume_waypoint"] = waypoint_index
        return self._append(event, "mission_resume", waypoint_index=waypoint_index)

    def connection_recovery(self, recovery_id: str, *, link: str = "lte") -> dict[str, Any]:
        event = self.get(recovery_id)
        event["connection"] = {"recovered": True, "link": link}
        return self._append(event, "connection_recovery", link=link)

    def sensor_reconfiguration(self, recovery_id: str, *, disabled: list[str] | None = None, enabled: list[str] | None = None) -> dict[str, Any]:
        event = self.get(recovery_id)
        event["sensors"] = {"disabled": list(disabled or []), "enabled": list(enabled or ["imu", "baro"])}
        return self._append(event, "sensor_reconfiguration", sensors=event["sensors"])

    def emergency_flight_mode(self, recovery_id: str, *, mode: str) -> dict[str, Any]:
        if mode not in EMERGENCY_MODES:
            raise ValidationError(f"mode must be one of {EMERGENCY_MODES}")
        event = self.get(recovery_id)
        event["mode"] = mode
        return self._append(event, "emergency_flight_mode", mode=mode)

    def complete(self, recovery_id: str, *, outcome: str = "safe") -> dict[str, Any]:
        event = self.get(recovery_id)
        event["status"] = "completed"
        event["outcome"] = outcome
        return self._append(event, "completed", outcome=outcome)

    def report(self, recovery_id: str) -> dict[str, Any]:
        event = self.get(recovery_id)
        return {
            "recovery_id": recovery_id,
            "aircraft_id": event["aircraft_id"],
            "reason": event["reason"],
            "mode": event["mode"],
            "status": event["status"],
            "outcome": event.get("outcome"),
            "timeline": event["timeline"],
            "steps": len(event["timeline"]),
            "generated_at": _now(),
        }

    def status(self) -> dict[str, Any]:
        return {"recovery": "1.0", "events": len(self.store.recovery_events.list_all()), "ready": True}


recovery_manager = RecoveryManager()
