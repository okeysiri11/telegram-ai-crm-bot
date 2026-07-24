"""Opportunity Detector — Sprint 22.1."""

from __future__ import annotations

from typing import Any

from platform_ai_business_advisor.models import OPPORTUNITY_KINDS


class OpportunityDetector:
    def detect(self, health: dict[str, Any]) -> dict[str, Any]:
        problems = set(health.get("problems") or [])
        found = []
        mapping = {
            "sales": "revenue_decline",
            "customers": "customer_decline",
            "repeat_visits": "repeat_visit_decline",
            "schedule_load": "open_booking_slots",
            "staff_efficiency": "underloaded_staff",
            "service_usage": "ineffective_services",
            "marketing_campaigns": "avg_check_decline",
            "profit": "revenue_decline",
        }
        for dim, kind in mapping.items():
            if dim in problems and kind in OPPORTUNITY_KINDS:
                found.append({"kind": kind, "source_dimension": dim, "severity": "high" if dim in ("sales", "customers") else "medium"})
        if "staff_efficiency" in problems:
            found.append({"kind": "overloaded_staff", "source_dimension": "staff_efficiency", "severity": "medium"})
        # de-dupe by kind
        uniq = {o["kind"]: o for o in found}
        opportunities = list(uniq.values())
        return {"opportunities": opportunities, "count": len(opportunities), "passed": True}
