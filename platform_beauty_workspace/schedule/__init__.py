"""Live schedule — Sprint 22.3."""

from __future__ import annotations

from typing import Any

from platform_beauty_workspace.models import SCHEDULE_VIEWS, STATUS_COLORS


class LiveSchedule:
    def __init__(self) -> None:
        self._items: list[dict[str, Any]] = []

    def render(self, *, view: str = "day", appointments: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        if view not in SCHEDULE_VIEWS:
            raise ValueError(f"unsupported schedule view: {view}")
        items = appointments if appointments is not None else self._items
        colored = [
            {
                **a,
                "color": STATUS_COLORS.get(a.get("status", "booked"), "#3B82F6"),
                "draggable": a.get("status") not in ("completed", "cancelled"),
            }
            for a in items
        ]
        return {
            "view": view,
            "views": list(SCHEDULE_VIEWS),
            "items": colored,
            "status_colors": dict(STATUS_COLORS),
            "supports_drag_drop": True,
            "calendar_ref": "enterprise_calendar",
            "conflict_prevention": True,
        }

    def move(
        self,
        appointment: dict[str, Any],
        *,
        start: str | None = None,
        end: str | None = None,
        employee_id: str | None = None,
        resource_id: str | None = None,
        existing: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        updated = dict(appointment)
        if start:
            updated["start"] = start
        if end:
            updated["end"] = end
        if employee_id:
            updated["employee_id"] = employee_id
        if resource_id:
            updated["resource_id"] = resource_id
        # conflict check against siblings sharing resource
        for other in existing or []:
            if other.get("appointment_id") == updated.get("appointment_id"):
                continue
            if other.get("status") == "cancelled":
                continue
            same_resource = updated.get("resource_id") and other.get("resource_id") == updated.get("resource_id")
            same_employee = updated.get("employee_id") and other.get("employee_id") == updated.get("employee_id")
            if not (same_resource or same_employee):
                continue
            o_start, o_end = other.get("start", ""), other.get("end", "")
            u_start, u_end = updated.get("start", ""), updated.get("end", "")
            if u_start and u_end and o_start and o_end:
                if not (u_end <= o_start or u_start >= o_end):
                    raise ValueError("schedule move conflict detected")
        updated["status"] = "rescheduled" if appointment.get("status") in ("booked", "confirmed") else updated.get("status")
        return updated
