from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


COMPONENT_TYPES = (
    "uav",
    "frame",
    "motor",
    "esc",
    "flight_controller",
    "gps",
    "compass",
    "telemetry_radio",
    "elrs",
    "receiver",
    "camera",
    "vtx",
    "antenna",
    "battery",
    "charger",
    "sensor",
    "payload",
    "servo",
    "power_module",
    "airspeed_sensor",
    "rangefinder",
    "companion_computer",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ComponentRecord:
    component_id: str
    component_type: str
    name: str
    manufacturer: str = ""
    model: str = ""
    specifications: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_id": self.component_id,
            "component_type": self.component_type,
            "name": self.name,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "specifications": dict(self.specifications),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class UAVRecord:
    uav_id: str
    name: str
    airframe_type: str = "multirotor"
    serial_number: str = ""
    frame_id: str = ""
    flight_controller_id: str = ""
    component_ids: list[str] = field(default_factory=list)
    status: str = "design"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "uav_id": self.uav_id,
            "name": self.name,
            "airframe_type": self.airframe_type,
            "serial_number": self.serial_number,
            "frame_id": self.frame_id,
            "flight_controller_id": self.flight_controller_id,
            "component_ids": list(self.component_ids),
            "status": self.status,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }
