"""Emergency management for mission operations (Sprint 11.7)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.store import DroneStore, drone_store


EMERGENCY_TYPES = (
    "emergency_landing",
    "lost_link",
    "gps_failure",
    "compass_failure",
    "battery_critical",
    "motor_failure",
    "sensor_failure",
    "mission_abort",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class EmergencyManager:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def trigger(
        self,
        *,
        emergency_type: str,
        fleet_id: str = "",
        ops_mission_id: str = "",
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        etype = emergency_type.lower().strip()
        eid = f"emg_{uuid.uuid4().hex[:12]}"
        actions = self._recommended_actions(etype)
        event = {
            "emergency_id": eid,
            "emergency_type": etype,
            "fleet_id": fleet_id,
            "ops_mission_id": ops_mission_id,
            "details": dict(details or {}),
            "actions": actions,
            "status": "active",
            "created_at": _now(),
        }
        self.store.emergency_events.save(eid, event)
        return event

    def _recommended_actions(self, emergency_type: str) -> list[str]:
        mapping = {
            "emergency_landing": ["select_lz", "descend", "disarm_after_land"],
            "lost_link": ["hold", "rtl_on_timeout", "attempt_relink"],
            "gps_failure": ["switch_visual_nav", "reduce_speed", "land_if_denied"],
            "compass_failure": ["use_gps_course", "avoid_yaw_critical"],
            "battery_critical": ["rtl", "land_nearest"],
            "motor_failure": ["stabilize", "land_immediate"],
            "sensor_failure": ["isolate_sensor", "failsafe_mode"],
            "mission_abort": ["abort_mission", "rtl_or_land"],
        }
        return mapping.get(emergency_type, ["assess", "notify_operator"])

    def automatic_recovery(self, emergency_id: str) -> dict[str, Any]:
        event = self.store.emergency_events.get(emergency_id)
        if event is None:
            from applications.drone_platform.shared.exceptions import NotFoundError

            raise NotFoundError("emergency_event", emergency_id)
        event["status"] = "recovering"
        event["recovery"] = {"started_at": _now(), "steps": event.get("actions", [])}
        self.store.emergency_events.save(emergency_id, event)
        return event

    def return_to_home(self, *, fleet_id: str, home: dict[str, float], current: dict[str, float], battery_pct: float) -> dict[str, Any]:
        viable = battery_pct >= 20
        return {
            "fleet_id": fleet_id,
            "home": home,
            "current": current,
            "battery_pct": battery_pct,
            "rth_viable": viable,
            "action": "rtl" if viable else "land_immediate",
            "manager": "return_to_home_manager",
            "at": _now(),
        }

    def list(self) -> list[dict[str, Any]]:
        return self.store.emergency_events.list_all()

    def status(self) -> dict[str, Any]:
        return {
            "emergency_management": "1.0",
            "types": list(EMERGENCY_TYPES),
            "event_count": self.store.emergency_events.count(),
            "capabilities": list(EMERGENCY_TYPES) + ["automatic_recovery", "return_to_home_manager"],
        }


emergency_manager = EmergencyManager()
