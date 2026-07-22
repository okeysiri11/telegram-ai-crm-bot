from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store

VEHICLE_TYPES = ("plane", "copter", "rover", "boat", "sub", "custom")

DEFAULT_MODES = {
    "plane": ["MANUAL", "FBWA", "AUTO", "RTL", "LOITER", "CRUISE"],
    "copter": ["STABILIZE", "ALT_HOLD", "LOITER", "AUTO", "RTL", "LAND", "GUIDED"],
    "rover": ["MANUAL", "STEERING", "HOLD", "AUTO", "RTL", "GUIDED"],
    "boat": ["MANUAL", "STEERING", "HOLD", "AUTO", "RTL"],
    "sub": ["MANUAL", "STABILIZE", "ALT_HOLD", "AUTO", "GUIDED"],
    "custom": ["MANUAL", "AUTO", "RTL"],
}

CORE_PARAMS = {
    "plane": {"ARSPD_ENABLE": 1, "TRIM_ARSPD_CM": 1500, "BATT_CAPACITY": 8000, "RTL_ALTITUDE": 100},
    "copter": {"FRAME_TYPE": 1, "ATC_RAT_PIT_P": 0.135, "BATT_CAPACITY": 5000, "FENCE_ENABLE": 1},
    "rover": {"CRUISE_SPEED": 2.0, "SPEED_TURN_GAIN": 2.0, "BATT_CAPACITY": 4000},
    "boat": {"CRUISE_SPEED": 1.5, "BATT_CAPACITY": 6000},
    "sub": {"SURFACE_MAX_DEPTH": 50, "BATT_CAPACITY": 10000},
    "custom": {"CUSTOM_FRAME": 1},
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ArduPilotService:
    """ArduPilot engineering workspace: projects, params, missions, modes, vehicles, branches."""

    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        if self.store.parameter_definitions.count() == 0:
            for vehicle, params in CORE_PARAMS.items():
                for name, default in params.items():
                    pid = f"apd_{vehicle}_{name}".lower()
                    self.store.parameter_definitions.save(
                        pid,
                        {
                            "definition_id": pid,
                            "name": name,
                            "vehicle": vehicle,
                            "default": default,
                            "description": f"ArduPilot {vehicle} parameter {name}",
                        },
                    )
        if self.store.flight_modes.count() == 0:
            for vehicle, modes in DEFAULT_MODES.items():
                for mode in modes:
                    mid = f"mode_{vehicle}_{mode}".lower()
                    self.store.flight_modes.save(
                        mid,
                        {"mode_id": mid, "vehicle": vehicle, "name": mode, "stack": "ardupilot"},
                    )

    def create_project(
        self,
        *,
        name: str,
        vehicle_type: str = "copter",
        branch: str = "master",
        version: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        vt = vehicle_type.lower()
        if vt not in VEHICLE_TYPES:
            raise ValidationError(f"Unsupported vehicle type: {vehicle_type}")
        pid = f"ap_{uuid.uuid4().hex[:12]}"
        record = {
            "ardupilot_project_id": pid,
            "name": name,
            "vehicle_type": vt,
            "branch": branch,
            "version": version,
            "parameters": dict(CORE_PARAMS.get(vt, {})),
            "metadata": dict(metadata or {}),
            "created_at": _now(),
        }
        self.store.ardupilot_projects.save(pid, record)
        return record

    def get_project(self, ardupilot_project_id: str) -> dict[str, Any]:
        item = self.store.ardupilot_projects.get(ardupilot_project_id)
        if item is None:
            raise NotFoundError("ardupilot_project", ardupilot_project_id)
        return item

    def list_projects(self) -> list[dict[str, Any]]:
        return self.store.ardupilot_projects.list_all()

    def parameter_database(self, vehicle: str | None = None) -> list[dict[str, Any]]:
        items = self.store.parameter_definitions.list_all()
        if vehicle:
            return [p for p in items if p.get("vehicle") == vehicle.lower()]
        return items

    def modes(self, vehicle: str | None = None) -> list[dict[str, Any]]:
        items = self.store.flight_modes.list_all()
        if vehicle:
            return [m for m in items if m.get("vehicle") == vehicle.lower()]
        return items

    def create_vehicle_profile(
        self,
        *,
        name: str,
        vehicle_type: str,
        parameters: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        vt = vehicle_type.lower()
        if vt not in VEHICLE_TYPES:
            raise ValidationError(f"Unsupported vehicle type: {vehicle_type}")
        vid = f"vp_{uuid.uuid4().hex[:12]}"
        base = dict(CORE_PARAMS.get(vt, {}))
        base.update(parameters or {})
        record = {
            "profile_id": vid,
            "name": name,
            "vehicle_type": vt,
            "parameters": base,
            "metadata": dict(metadata or {}),
            "created_at": _now(),
        }
        self.store.vehicle_profiles.save(vid, record)
        return record

    def list_vehicle_profiles(self) -> list[dict[str, Any]]:
        return self.store.vehicle_profiles.list_all()

    def add_mission_template(
        self,
        *,
        name: str,
        vehicle_type: str,
        waypoints: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        mid = f"ml_{uuid.uuid4().hex[:12]}"
        record = {
            "mission_library_id": mid,
            "name": name,
            "vehicle_type": vehicle_type.lower(),
            "waypoints": list(waypoints or []),
            "metadata": dict(metadata or {}),
            "created_at": _now(),
        }
        self.store.mission_library.save(mid, record)
        return record

    def list_mission_library(self) -> list[dict[str, Any]]:
        return self.store.mission_library.list_all()

    def create_branch(
        self,
        *,
        name: str,
        base: str = "master",
        ardupilot_project_id: str = "",
        notes: str = "",
    ) -> dict[str, Any]:
        bid = f"br_{uuid.uuid4().hex[:12]}"
        record = {
            "branch_id": bid,
            "name": name,
            "base": base,
            "ardupilot_project_id": ardupilot_project_id,
            "notes": notes,
            "created_at": _now(),
        }
        self.store.firmware_branches.save(bid, record)
        return record

    def list_branches(self) -> list[dict[str, Any]]:
        return self.store.firmware_branches.list_all()

    def supported_vehicles(self) -> list[str]:
        return list(VEHICLE_TYPES)


ardupilot_service = ArduPilotService()
