from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Waypoint:
    sequence: int
    latitude: float
    longitude: float
    altitude_m: float
    command: str = "WAYPOINT"
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude_m": self.altitude_m,
            "command": self.command,
            "params": dict(self.params),
        }


@dataclass
class Geofence:
    name: str
    vertices: list[dict[str, float]] = field(default_factory=list)
    max_altitude_m: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "vertices": list(self.vertices),
            "max_altitude_m": self.max_altitude_m,
        }


@dataclass
class FlightProfile:
    name: str
    cruise_speed_mps: float = 10.0
    max_altitude_m: float = 120.0
    settings: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "cruise_speed_mps": self.cruise_speed_mps,
            "max_altitude_m": self.max_altitude_m,
            "settings": dict(self.settings),
        }


@dataclass
class Mission:
    mission_id: str
    name: str
    uav_id: str = ""
    waypoints: list[dict[str, Any]] = field(default_factory=list)
    rally_points: list[dict[str, Any]] = field(default_factory=list)
    geofences: list[dict[str, Any]] = field(default_factory=list)
    payload_configuration: dict[str, Any] = field(default_factory=dict)
    flight_profile: dict[str, Any] = field(default_factory=dict)
    is_template: bool = False
    history: list[dict[str, Any]] = field(default_factory=list)
    status: str = "draft"
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "name": self.name,
            "uav_id": self.uav_id,
            "waypoints": list(self.waypoints),
            "rally_points": list(self.rally_points),
            "geofences": list(self.geofences),
            "payload_configuration": dict(self.payload_configuration),
            "flight_profile": dict(self.flight_profile),
            "is_template": self.is_template,
            "history": list(self.history),
            "status": self.status,
            "created_at": self.created_at,
        }
