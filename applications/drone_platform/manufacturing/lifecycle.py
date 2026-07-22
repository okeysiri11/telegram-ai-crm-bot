"""Aircraft lifecycle tracking (Sprint 11.6)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class LifecycleTracker:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def register_aircraft(
        self,
        *,
        serial_number: str,
        model: str,
        unique_aircraft_id: str | None = None,
        order_id: str = "",
    ) -> dict[str, Any]:
        uaid = unique_aircraft_id or f"AID-{uuid.uuid4().hex[:10].upper()}"
        record = {
            "aircraft_id": uaid,
            "serial_number": serial_number,
            "model": model,
            "order_id": order_id,
            "manufacturing_history": [{"event": "registered", "at": _now()}],
            "repair_history": [],
            "firmware_history": [],
            "owner_history": [],
            "maintenance_history": [],
            "incident_history": [],
            "flight_hours": 0.0,
            "battery_cycles": 0,
            "status": "in_service",
            "created_at": _now(),
        }
        self.store.aircraft_lifecycle.save(uaid, record)
        return record

    def get(self, aircraft_id: str) -> dict[str, Any]:
        item = self.store.aircraft_lifecycle.get(aircraft_id)
        if item is None:
            raise NotFoundError("aircraft_lifecycle", aircraft_id)
        return item

    def get_by_serial(self, serial_number: str) -> dict[str, Any]:
        for item in self.store.aircraft_lifecycle.list_all():
            if item.get("serial_number") == serial_number:
                return item
        raise NotFoundError("aircraft_lifecycle", serial_number)

    def add_event(self, aircraft_id: str, *, bucket: str, event: dict[str, Any]) -> dict[str, Any]:
        record = self.get(aircraft_id)
        key = f"{bucket}_history" if not bucket.endswith("_history") else bucket
        if key not in record:
            raise ValidationError(f"Unknown history bucket: {bucket}")
        entry = {**event, "at": event.get("at") or _now()}
        record[key].append(entry)
        self.store.aircraft_lifecycle.save(aircraft_id, record)
        return record

    def add_flight_hours(self, aircraft_id: str, hours: float) -> dict[str, Any]:
        record = self.get(aircraft_id)
        record["flight_hours"] = round(float(record.get("flight_hours", 0)) + hours, 2)
        record["maintenance_history"].append({"event": "flight_hours_added", "hours": hours, "at": _now()})
        self.store.aircraft_lifecycle.save(aircraft_id, record)
        return record

    def add_battery_cycles(self, aircraft_id: str, cycles: int = 1) -> dict[str, Any]:
        record = self.get(aircraft_id)
        record["battery_cycles"] = int(record.get("battery_cycles", 0)) + cycles
        self.store.aircraft_lifecycle.save(aircraft_id, record)
        return record

    def end_of_life(self, aircraft_id: str, *, reason: str = "retired") -> dict[str, Any]:
        record = self.get(aircraft_id)
        record["status"] = "end_of_life"
        record["eol"] = {"reason": reason, "at": _now()}
        record["manufacturing_history"].append({"event": "eol", "reason": reason, "at": _now()})
        self.store.aircraft_lifecycle.save(aircraft_id, record)
        return record

    def list(self) -> list[dict[str, Any]]:
        return self.store.aircraft_lifecycle.list_all()

    def status(self) -> dict[str, Any]:
        return {
            "lifecycle_tracking": "1.0",
            "aircraft_count": self.store.aircraft_lifecycle.count(),
            "capabilities": [
                "unique_aircraft_id",
                "serial_numbers",
                "manufacturing_history",
                "repair_history",
                "firmware_history",
                "owner_history",
                "maintenance_history",
                "flight_hours",
                "battery_cycles",
                "incident_history",
                "end_of_life",
            ],
        }


lifecycle_tracker = LifecycleTracker()
