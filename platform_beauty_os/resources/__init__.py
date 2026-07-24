"""Resource management — Sprint 22.2."""

from __future__ import annotations

from typing import Any

from platform_beauty_os.models import RESOURCE_KINDS


class ResourceManagement:
    def __init__(self) -> None:
        self._bookings: list[dict[str, Any]] = []

    def create(self, *, name: str, kind: str, branch: str = "") -> dict[str, Any]:
        if kind not in RESOURCE_KINDS:
            raise ValueError(f"unknown resource kind: {kind}")
        if not name:
            raise ValueError("resource name is required")
        return {"name": name, "kind": kind, "branch": branch, "available": True}

    def book(self, *, resource_id: str, start: str, end: str, appointment_id: str) -> dict[str, Any]:
        for b in self._bookings:
            if b["resource_id"] == resource_id and not (end <= b["start"] or start >= b["end"]):
                raise ValueError("resource booking conflict")
        booking = {
            "resource_id": resource_id,
            "start": start,
            "end": end,
            "appointment_id": appointment_id,
            "calendar_ref": "enterprise_calendar",
        }
        self._bookings.append(booking)
        return {"booked": True, **booking, "conflict": False}

    def status(self) -> dict[str, Any]:
        return {"bookings": len(self._bookings)}
