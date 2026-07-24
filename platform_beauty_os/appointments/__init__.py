"""Appointment engine — Sprint 22.2."""

from __future__ import annotations

from typing import Any

from platform_beauty_os.models import APPOINTMENT_STATUSES


class AppointmentEngine:
    TRANSITIONS = {
        "booked": {"confirmed", "rescheduled", "cancelled", "waiting"},
        "confirmed": {"completed", "cancelled", "rescheduled", "rebooked"},
        "waiting": {"confirmed", "cancelled"},
        "rescheduled": {"confirmed", "cancelled"},
        "rebooked": {"confirmed", "cancelled"},
        "cancelled": set(),
        "completed": {"rebooked"},
    }

    def create(
        self,
        *,
        customer_id: str,
        service_id: str,
        employee_id: str,
        branch_id: str,
        start: str,
        end: str,
        resource_id: str = "",
    ) -> dict[str, Any]:
        if not all([customer_id, service_id, employee_id, branch_id, start, end]):
            raise ValueError("appointment fields incomplete")
        return {
            "customer_id": customer_id,
            "service_id": service_id,
            "employee_id": employee_id,
            "branch_id": branch_id,
            "resource_id": resource_id,
            "start": start,
            "end": end,
            "status": "booked",
            "calendar_ref": "enterprise_calendar",
            "finance_ref": "enterprise_finance",
        }

    def transition(self, appointment: dict[str, Any], *, status: str) -> dict[str, Any]:
        if status not in APPOINTMENT_STATUSES:
            raise ValueError(f"unknown appointment status: {status}")
        current = appointment.get("status", "booked")
        allowed = self.TRANSITIONS.get(current, set())
        if status not in allowed:
            raise ValueError(f"cannot transition {current} -> {status}")
        return {**appointment, "status": status}
