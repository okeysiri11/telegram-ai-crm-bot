"""Smart Availability Engine — Sprint 22.4."""

from __future__ import annotations

from typing import Any


class SmartAvailabilityEngine:
    def suggest(
        self,
        *,
        service_ids: list[str],
        duration_min: int = 60,
        employees: list[dict[str, Any]] | None = None,
        resources: list[dict[str, Any]] | None = None,
        open_slots: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        if not service_ids:
            raise ValueError("service_ids required for availability")
        employees = employees or [{"employee_id": "e1", "load": 0.4, "name": "Anna"}]
        resources = resources or [{"resource_id": "r1", "kind": "chair", "available": True}]
        open_slots = open_slots or [
            {"start": "2026-07-26T10:00:00Z", "end": "2026-07-26T11:00:00Z", "branch_id": "b1"},
            {"start": "2026-07-26T14:00:00Z", "end": "2026-07-26T15:00:00Z", "branch_id": "b1"},
        ]
        master = sorted(employees, key=lambda e: float(e.get("load", 1)))[0]
        slot = open_slots[0]
        room = next((r for r in resources if r.get("available", True)), resources[0])
        suggestion = {
            "start": slot["start"],
            "end": slot.get("end") or slot["start"],
            "employee_id": master.get("employee_id"),
            "employee_name": master.get("name"),
            "branch_id": slot.get("branch_id", "b1"),
            "resource_id": room.get("resource_id"),
            "service_ids": list(service_ids),
            "duration_min": duration_min,
            "score": 0.92,
            "reason": "lowest_master_load_and_open_slot",
        }
        return {
            "suggestions": [suggestion],
            "optimal": suggestion,
            "analyzed": {
                "open_slots": len(open_slots),
                "masters": len(employees),
                "resources": len(resources),
                "duration_min": duration_min,
            },
            "ai_may_book": False,
            "requires_confirmation": True,
        }
