"""Beauty dashboard — Sprint 22.2."""

from __future__ import annotations

from typing import Any


class BeautyDashboard:
    def render(
        self,
        *,
        appointments: list[dict[str, Any]],
        customers: list[dict[str, Any]],
        employees: list[dict[str, Any]],
        services: list[dict[str, Any]],
        advisor_brief: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        booked = [a for a in appointments if a.get("status") in ("booked", "confirmed", "waiting")]
        completed = [a for a in appointments if a.get("status") == "completed"]
        revenue = sum(float(s.get("price", 0)) for s in services) * max(len(completed), 1) * 0.3
        avg_check = revenue / max(len(completed), 1)
        return {
            "revenue": round(revenue, 2),
            "bookings": len(booked),
            "master_load": round(min(1.0, len(booked) / max(len(employees), 1)), 2),
            "open_slots": max(0, len(employees) * 8 - len(booked)),
            "new_customers": len(customers),
            "returning_customers": sum(1 for c in customers if len(c.get("visit_history") or []) > 1),
            "average_check": round(avg_check, 2),
            "ai_recommendations": (advisor_brief or {}).get("recommended_actions")
            or (advisor_brief or {}).get("recommendations")
            or [],
            "advisor_ref": "ai_business_advisor",
            "finance_ref": "enterprise_finance",
            "status": "ready",
        }
