from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.models.missions import Mission
from applications.drone_platform.shared.exceptions import NotFoundError
from applications.drone_platform.shared.store import DroneStore, drone_store


class MissionService:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def create_mission(
        self,
        *,
        name: str,
        uav_id: str = "",
        waypoints: list[dict[str, Any]] | None = None,
        rally_points: list[dict[str, Any]] | None = None,
        geofences: list[dict[str, Any]] | None = None,
        payload_configuration: dict[str, Any] | None = None,
        flight_profile: dict[str, Any] | None = None,
        is_template: bool = False,
        mission_id: str | None = None,
    ) -> Mission:
        mid = mission_id or f"msn_{uuid.uuid4().hex[:12]}"
        mission = Mission(
            mission_id=mid,
            name=name,
            uav_id=uav_id,
            waypoints=list(waypoints or []),
            rally_points=list(rally_points or []),
            geofences=list(geofences or []),
            payload_configuration=dict(payload_configuration or {}),
            flight_profile=dict(flight_profile or {}),
            is_template=is_template,
            history=[{"event": "created", "at": datetime.now(timezone.utc).isoformat()}],
        )
        self.store.missions.save(mid, mission)
        return mission

    def get_mission(self, mission_id: str) -> Mission:
        item = self.store.missions.get(mission_id)
        if item is None:
            raise NotFoundError("mission", mission_id)
        return item

    def list_missions(self, *, templates_only: bool = False) -> list[Mission]:
        items = self.store.missions.list_all()
        if templates_only:
            return [m for m in items if m.is_template]
        return items

    def add_waypoint(self, mission_id: str, waypoint: dict[str, Any]) -> Mission:
        mission = self.get_mission(mission_id)
        if "sequence" not in waypoint:
            waypoint = {**waypoint, "sequence": len(mission.waypoints) + 1}
        mission.waypoints.append(waypoint)
        mission.history.append({"event": "waypoint_added", "at": datetime.now(timezone.utc).isoformat()})
        self.store.missions.save(mission_id, mission)
        return mission

    def set_geofences(self, mission_id: str, geofences: list[dict[str, Any]]) -> Mission:
        mission = self.get_mission(mission_id)
        mission.geofences = list(geofences)
        mission.history.append({"event": "geofences_updated", "at": datetime.now(timezone.utc).isoformat()})
        self.store.missions.save(mission_id, mission)
        return mission

    def set_rally_points(self, mission_id: str, rally_points: list[dict[str, Any]]) -> Mission:
        mission = self.get_mission(mission_id)
        mission.rally_points = list(rally_points)
        mission.history.append({"event": "rally_updated", "at": datetime.now(timezone.utc).isoformat()})
        self.store.missions.save(mission_id, mission)
        return mission

    def clone_as_template(self, mission_id: str, template_name: str) -> Mission:
        source = self.get_mission(mission_id)
        return self.create_mission(
            name=template_name,
            uav_id="",
            waypoints=list(source.waypoints),
            rally_points=list(source.rally_points),
            geofences=list(source.geofences),
            payload_configuration=dict(source.payload_configuration),
            flight_profile=dict(source.flight_profile),
            is_template=True,
        )


mission_service = MissionService()
