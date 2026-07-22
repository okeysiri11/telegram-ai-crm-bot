"""Fleet management — registry, assignments, readiness (Sprint 11.7)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class FleetManager:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def register_aircraft(
        self,
        *,
        name: str,
        serial_number: str = "",
        model: str = "",
        status: str = "available",
        maintenance_status: str = "ok",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        fid = f"flt_{uuid.uuid4().hex[:12]}"
        item = {
            "fleet_id": fid,
            "name": name,
            "serial_number": serial_number or f"SN-{uuid.uuid4().hex[:8].upper()}",
            "model": model,
            "status": status,
            "maintenance_status": maintenance_status,
            "mission_readiness": "ready" if status == "available" and maintenance_status == "ok" else "not_ready",
            "assignments": {},
            "metadata": dict(metadata or {}),
            "created_at": _now(),
        }
        self.store.fleet_aircraft.save(fid, item)
        return item

    def get(self, fleet_id: str) -> dict[str, Any]:
        item = self.store.fleet_aircraft.get(fleet_id)
        if item is None:
            raise NotFoundError("fleet_aircraft", fleet_id)
        return item

    def list(self) -> list[dict[str, Any]]:
        return self.store.fleet_aircraft.list_all()

    def assign(
        self,
        fleet_id: str,
        *,
        pilot_id: str = "",
        payload_id: str = "",
        battery_id: str = "",
        equipment: list[str] | None = None,
        ops_mission_id: str = "",
    ) -> dict[str, Any]:
        aircraft = self.get(fleet_id)
        assignment = {
            "assignment_id": f"asg_{uuid.uuid4().hex[:12]}",
            "fleet_id": fleet_id,
            "pilot_id": pilot_id,
            "payload_id": payload_id,
            "battery_id": battery_id,
            "equipment": list(equipment or []),
            "ops_mission_id": ops_mission_id,
            "at": _now(),
        }
        aircraft["assignments"] = assignment
        aircraft["status"] = "assigned" if ops_mission_id or pilot_id else aircraft["status"]
        self.store.fleet_aircraft.save(fleet_id, aircraft)
        self.store.fleet_assignments.save(assignment["assignment_id"], assignment)
        return assignment

    def set_availability(self, fleet_id: str, *, available: bool) -> dict[str, Any]:
        aircraft = self.get(fleet_id)
        aircraft["status"] = "available" if available else "unavailable"
        aircraft["mission_readiness"] = "ready" if available and aircraft.get("maintenance_status") == "ok" else "not_ready"
        self.store.fleet_aircraft.save(fleet_id, aircraft)
        return aircraft

    def set_maintenance(self, fleet_id: str, *, maintenance_status: str) -> dict[str, Any]:
        aircraft = self.get(fleet_id)
        aircraft["maintenance_status"] = maintenance_status
        aircraft["mission_readiness"] = "ready" if aircraft.get("status") == "available" and maintenance_status == "ok" else "not_ready"
        self.store.fleet_aircraft.save(fleet_id, aircraft)
        return aircraft

    def readiness(self, fleet_id: str) -> dict[str, Any]:
        aircraft = self.get(fleet_id)
        ready = aircraft.get("mission_readiness") == "ready"
        return {
            "fleet_id": fleet_id,
            "ready": ready,
            "status": aircraft.get("status"),
            "maintenance_status": aircraft.get("maintenance_status"),
            "mission_readiness": aircraft.get("mission_readiness"),
            "assignments": aircraft.get("assignments") or {},
        }

    def available_aircraft(self) -> list[dict[str, Any]]:
        return [a for a in self.list() if a.get("status") == "available" and a.get("mission_readiness") == "ready"]

    def status(self) -> dict[str, Any]:
        return {
            "fleet_management": "1.0",
            "aircraft": self.store.fleet_aircraft.count(),
            "assignments": self.store.fleet_assignments.count(),
            "capabilities": [
                "fleet_registry",
                "aircraft_assignment",
                "pilot_assignment",
                "payload_assignment",
                "availability_manager",
                "maintenance_status",
                "mission_readiness",
                "battery_assignment",
                "equipment_assignment",
            ],
        }


fleet_manager = FleetManager()
