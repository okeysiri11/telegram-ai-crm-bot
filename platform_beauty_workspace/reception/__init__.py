"""Reception dashboard — Sprint 22.3."""

from __future__ import annotations

from typing import Any


class ReceptionDashboard:
    def render(
        self,
        *,
        appointments: list[dict[str, Any]],
        employees: list[dict[str, Any]],
        admin_tasks: list[dict[str, Any]] | None = None,
        advisor_recommendations: list[str] | None = None,
        open_slots: int = 0,
    ) -> dict[str, Any]:
        today = [a for a in appointments if a.get("status") not in ("cancelled",)]
        current = [a for a in appointments if a.get("status") == "confirmed"]
        waiting = [a for a in appointments if a.get("status") == "waiting"]
        cancelled = [a for a in appointments if a.get("status") == "cancelled"]
        load = round(min(1.0, len(today) / max(len(employees) * 8, 1)), 2)
        return {
            "todays_appointments": today,
            "current_clients": current,
            "waiting_clients": waiting,
            "cancelled_appointments": cancelled,
            "open_slots": open_slots,
            "master_load": load,
            "admin_tasks": list(admin_tasks or [{"task": "confirm_arrivals", "priority": "high"}]),
            "ai_recommendations": list(advisor_recommendations or []),
            "advisor_ref": "ai_business_advisor",
            "beauty_os_ref": "beauty_os",
            "realtime": True,
            "status": "ready",
        }
