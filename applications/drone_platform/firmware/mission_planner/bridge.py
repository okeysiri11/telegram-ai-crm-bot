from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.missions.service import MissionService, mission_service
from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MissionPlannerBridge:
    """Mission Planner integration bridge for engineering import/export and editors."""

    def __init__(self, store: DroneStore | None = None, missions: MissionService | None = None) -> None:
        self.store = store or drone_store
        self.missions = missions or mission_service

    def sync_parameters(self, config_id: str, parameter_set_payload: dict[str, Any]) -> dict[str, Any]:
        """Synchronize a Mission Planner parameter set into configuration store."""
        cid = config_id or f"mpc_{uuid.uuid4().hex[:12]}"
        record = {
            "config_id": cid,
            "name": parameter_set_payload.get("name", "mp-sync"),
            "profile": "mission_planner",
            "firmware_project_id": parameter_set_payload.get("firmware_project_id", ""),
            "parameters": dict(parameter_set_payload.get("parameters") or {}),
            "metadata": {"source": "mission_planner", "synced_at": _now()},
            "created_at": _now(),
        }
        self.store.firmware_configs.save(cid, record)
        return {"status": "synced", "config": record}

    def import_mission(self, payload: dict[str, Any] | str) -> dict[str, Any]:
        data = json.loads(payload) if isinstance(payload, str) else payload
        mission = self.missions.create_mission(
            name=data.get("name", "Imported Mission"),
            uav_id=data.get("uav_id", ""),
            waypoints=data.get("waypoints"),
            rally_points=data.get("rally_points"),
            geofences=data.get("geofences"),
            payload_configuration=data.get("payload_configuration"),
            flight_profile=data.get("flight_profile"),
            is_template=bool(data.get("is_template", False)),
        )
        return {"status": "imported", "mission": mission.to_dict()}

    def export_mission(self, mission_id: str) -> str:
        mission = self.missions.get_mission(mission_id)
        return json.dumps(mission.to_dict(), indent=2, sort_keys=True)

    def edit_waypoints(self, mission_id: str, waypoints: list[dict[str, Any]]) -> dict[str, Any]:
        mission = self.missions.get_mission(mission_id)
        mission.waypoints = list(waypoints)
        mission.history.append({"event": "waypoints_edited", "at": _now(), "source": "mission_planner"})
        self.store.missions.save(mission_id, mission)
        return mission.to_dict()

    def edit_geofence(self, mission_id: str, geofences: list[dict[str, Any]]) -> dict[str, Any]:
        return self.missions.set_geofences(mission_id, geofences).to_dict()

    def edit_rally_points(self, mission_id: str, rally_points: list[dict[str, Any]]) -> dict[str, Any]:
        return self.missions.set_rally_points(mission_id, rally_points).to_dict()

    def save_flight_mode_profile(
        self,
        *,
        name: str,
        modes: list[str],
        vehicle_type: str = "copter",
    ) -> dict[str, Any]:
        pid = f"mpf_{uuid.uuid4().hex[:12]}"
        record = {
            "profile_id": pid,
            "name": name,
            "vehicle_type": vehicle_type,
            "modes": list(modes),
            "created_at": _now(),
            "source": "mission_planner",
        }
        self.store.mp_profiles.save(pid, record)
        return record

    def save_configuration_profile(
        self,
        *,
        name: str,
        parameters: dict[str, Any],
        notes: str = "",
    ) -> dict[str, Any]:
        pid = f"mpc_{uuid.uuid4().hex[:12]}"
        record = {
            "profile_id": pid,
            "name": name,
            "parameters": dict(parameters),
            "notes": notes,
            "created_at": _now(),
            "source": "mission_planner",
        }
        self.store.mp_profiles.save(pid, record)
        return record

    def list_profiles(self) -> list[dict[str, Any]]:
        return self.store.mp_profiles.list_all()

    def mission_templates(self) -> list[dict[str, Any]]:
        return [m.to_dict() for m in self.missions.list_missions(templates_only=True)]


mission_planner_bridge = MissionPlannerBridge()
