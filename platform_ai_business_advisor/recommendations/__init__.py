"""Recommendation Engine — Sprint 22.1."""

from __future__ import annotations

from typing import Any

from platform_ai_business_advisor.models import COMMERCIAL_ACTIONS, RECOMMENDATION_KINDS


class RecommendationEngine:
    KIND_MAP = {
        "revenue_decline": "launch_promotion",
        "customer_decline": "winback_customers",
        "avg_check_decline": "adjust_prices",
        "repeat_visit_decline": "loyalty_program",
        "open_booking_slots": "send_newsletter",
        "overloaded_staff": "offer_discount",
        "underloaded_staff": "run_ad_campaign",
        "ineffective_services": "create_reels",
    }

    def recommend(self, opportunities: dict[str, Any]) -> dict[str, Any]:
        items = []
        for opp in opportunities.get("opportunities") or []:
            kind = self.KIND_MAP.get(opp["kind"], "launch_promotion")
            if kind not in RECOMMENDATION_KINDS:
                kind = "launch_promotion"
            items.append(
                {
                    "kind": kind,
                    "opportunity": opp["kind"],
                    "requires_owner_approval": True,
                    "commercial_impact": list(COMMERCIAL_ACTIONS),
                    "ai_may_execute": False,
                    "expected_effect": {"revenue_lift_pct": 0.08, "retention_lift_pct": 0.05},
                }
            )
        if not items:
            items.append(
                {
                    "kind": "send_newsletter",
                    "opportunity": "maintenance",
                    "requires_owner_approval": True,
                    "commercial_impact": ["marketing", "customers"],
                    "ai_may_execute": False,
                    "expected_effect": {"revenue_lift_pct": 0.03, "retention_lift_pct": 0.02},
                }
            )
        return {"recommendations": items, "count": len(items), "ai_executes_automatically": False, "passed": True}
