"""Unified Digital Twin — aircraft, battery, payload, mission, production, engineering, cloud, fleet (Sprint 11.10)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


TWIN_TYPES = (
    "aircraft",
    "battery",
    "payload",
    "mission",
    "production",
    "engineering",
    "cloud",
    "fleet",
)


class UnifiedDigitalTwin:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def create(self, *, twin_type: str, name: str, source_id: str = "", state: dict[str, Any] | None = None) -> dict[str, Any]:
        if twin_type not in TWIN_TYPES:
            raise ValidationError(f"twin_type must be one of {TWIN_TYPES}")
        if not name:
            raise ValidationError("name required")
        tid = f"utwin_{uuid.uuid4().hex[:12]}"
        twin = {
            "twin_id": tid,
            "twin_type": twin_type,
            "name": name,
            "source_id": source_id,
            "state": dict(state or {}),
            "synced": False,
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.unified_twins.save(tid, twin)
        return twin

    def get(self, twin_id: str) -> dict[str, Any]:
        item = self.store.unified_twins.get(twin_id)
        if item is None:
            raise NotFoundError("unified_twin", twin_id)
        return item

    def sync(self, twin_id: str, *, state: dict[str, Any]) -> dict[str, Any]:
        twin = self.get(twin_id)
        twin["state"] = {**twin.get("state", {}), **state}
        twin["synced"] = True
        twin["updated_at"] = _now()
        self.store.unified_twins.save(twin_id, twin)
        return twin

    def sync_all(self) -> dict[str, Any]:
        twins = self.store.unified_twins.list_all()
        for twin in twins:
            twin["synced"] = True
            twin["updated_at"] = _now()
            self.store.unified_twins.save(twin["twin_id"], twin)
        return {"synced": len(twins), "at": _now()}

    def list_twins(self, *, twin_type: str | None = None) -> list[dict[str, Any]]:
        items = self.store.unified_twins.list_all()
        if twin_type:
            items = [i for i in items if i.get("twin_type") == twin_type]
        return items

    def status(self) -> dict[str, Any]:
        return {"unified_digital_twin": "1.0", "types": list(TWIN_TYPES), "twins": len(self.list_twins()), "ready": True}


unified_digital_twin = UnifiedDigitalTwin()
