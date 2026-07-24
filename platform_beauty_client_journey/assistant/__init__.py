"""AI Booking Assistant — Sprint 22.4."""

from __future__ import annotations

from typing import Any


class AIBookingAssistant:
    def recommend(
        self,
        *,
        availability: dict[str, Any],
        journey: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        optimal = (availability or {}).get("optimal") or {}
        return {
            "best_time": optimal.get("start"),
            "best_master": optimal.get("employee_name") or optimal.get("employee_id"),
            "upsell_services": ["scalp_massage", "hair_mask"],
            "retail_products": ["shampoo_home_care"],
            "avg_check_lift_pct": 0.12,
            "loyalty_level": (journey or {}).get("loyalty_level", "new"),
            "ai_may_execute": False,
            "proposes_only": True,
            "requires_confirmation": True,
            "advisor_ref": "ai_business_advisor",
            "product_intelligence_ref": "product_intelligence",
        }
