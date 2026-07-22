"""Lifecycle Intelligence — full aircraft digital lifecycle (Sprint 11.10)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


LIFECYCLE_STAGES = (
    "design",
    "simulation",
    "prototype",
    "production",
    "programming",
    "calibration",
    "testing",
    "deployment",
    "operations",
    "maintenance",
    "modernization",
    "retirement",
)


class LifecycleIntelligence:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def start(self, *, aircraft_id: str, stage: str = "design", metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        if not aircraft_id:
            raise ValidationError("aircraft_id required")
        if stage not in LIFECYCLE_STAGES:
            raise ValidationError(f"stage must be one of {LIFECYCLE_STAGES}")
        lid = f"life_{uuid.uuid4().hex[:12]}"
        item = {
            "lifecycle_id": lid,
            "aircraft_id": aircraft_id,
            "stage": stage,
            "history": [{"stage": stage, "at": _now()}],
            "complete": False,
            "metadata": dict(metadata or {}),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.aircraft_lifecycles_eco.save(lid, item)
        return item

    def get(self, lifecycle_id: str) -> dict[str, Any]:
        item = self.store.aircraft_lifecycles_eco.get(lifecycle_id)
        if item is None:
            raise NotFoundError("aircraft_lifecycle", lifecycle_id)
        return item

    def advance(self, lifecycle_id: str, *, stage: str | None = None) -> dict[str, Any]:
        item = self.get(lifecycle_id)
        current = item["stage"]
        if stage is None:
            idx = LIFECYCLE_STAGES.index(current)
            if idx >= len(LIFECYCLE_STAGES) - 1:
                item["complete"] = True
                item["updated_at"] = _now()
                self.store.aircraft_lifecycles_eco.save(lifecycle_id, item)
                return item
            stage = LIFECYCLE_STAGES[idx + 1]
        if stage not in LIFECYCLE_STAGES:
            raise ValidationError(f"stage must be one of {LIFECYCLE_STAGES}")
        item["stage"] = stage
        item["history"].append({"stage": stage, "at": _now()})
        item["complete"] = stage == "retirement"
        item["updated_at"] = _now()
        self.store.aircraft_lifecycles_eco.save(lifecycle_id, item)
        return item

    def timeline(self, lifecycle_id: str) -> dict[str, Any]:
        item = self.get(lifecycle_id)
        return {
            "lifecycle_id": lifecycle_id,
            "aircraft_id": item["aircraft_id"],
            "stage": item["stage"],
            "history": item["history"],
            "stages": list(LIFECYCLE_STAGES),
            "complete": item.get("complete", False),
        }

    def list_for_aircraft(self, aircraft_id: str) -> list[dict[str, Any]]:
        return [x for x in self.store.aircraft_lifecycles_eco.list_all() if x.get("aircraft_id") == aircraft_id]

    def status(self) -> dict[str, Any]:
        return {
            "lifecycle_intelligence": "1.0",
            "stages": list(LIFECYCLE_STAGES),
            "records": len(self.store.aircraft_lifecycles_eco.list_all()),
            "ready": True,
        }


lifecycle_intelligence = LifecycleIntelligence()
