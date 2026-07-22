"""Digital Twin — aircraft, battery, mission, maintenance, engineering with live sync (Sprint 11.8)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DigitalTwinService:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def create_twin(
        self,
        *,
        twin_type: str,
        name: str,
        source_id: str = "",
        state: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        allowed = {"aircraft", "battery", "mission", "maintenance", "engineering"}
        if twin_type not in allowed:
            raise ValidationError(f"twin_type must be one of {sorted(allowed)}")
        if not name:
            raise ValidationError("twin name required")
        tid = f"twin_{uuid.uuid4().hex[:12]}"
        twin = {
            "twin_id": tid,
            "twin_type": twin_type,
            "name": name,
            "source_id": source_id,
            "state": dict(state or {}),
            "synced": False,
            "metadata": dict(metadata or {}),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.digital_twins.save(tid, twin)
        return twin

    def get(self, twin_id: str) -> dict[str, Any]:
        item = self.store.digital_twins.get(twin_id)
        if item is None:
            raise NotFoundError("digital_twin", twin_id)
        return item

    def aircraft_twin(self, *, name: str, aircraft_id: str = "", state: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.create_twin(twin_type="aircraft", name=name, source_id=aircraft_id, state=state or {"mode": "STANDBY", "battery_pct": 100})

    def battery_twin(self, *, name: str, battery_id: str = "", state: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.create_twin(twin_type="battery", name=name, source_id=battery_id, state=state or {"soh": 0.98, "cycles": 12})

    def mission_twin(self, *, name: str, mission_id: str = "", state: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.create_twin(twin_type="mission", name=name, source_id=mission_id, state=state or {"progress": 0})

    def maintenance_twin(self, *, name: str, asset_id: str = "", state: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.create_twin(twin_type="maintenance", name=name, source_id=asset_id, state=state or {"next_service_h": 50})

    def engineering_twin(self, *, name: str, project_id: str = "", state: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.create_twin(twin_type="engineering", name=name, source_id=project_id, state=state or {"revision": "A"})

    def live_sync(self, twin_id: str, *, state: dict[str, Any]) -> dict[str, Any]:
        twin = self.get(twin_id)
        twin["state"] = {**twin.get("state", {}), **state}
        twin["synced"] = True
        twin["updated_at"] = _now()
        self.store.digital_twins.save(twin_id, twin)
        return twin

    def list_twins(self, *, twin_type: str | None = None) -> list[dict[str, Any]]:
        items = self.store.digital_twins.list_all()
        if twin_type:
            items = [i for i in items if i.get("twin_type") == twin_type]
        return items

    def status(self) -> dict[str, Any]:
        return {"digital_twin": "1.0", "twins": len(self.list_twins()), "ready": True}


digital_twin_service = DigitalTwinService()
