"""AI Beauty Assistant — Sprint 22.8."""

from __future__ import annotations

from typing import Any


class AIBeautyAssistant:
    def recommend(
        self,
        *,
        account: dict[str, Any] | None = None,
        loyalty: dict[str, Any] | None = None,
        memberships: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        account = account or {}
        loyalty = loyalty or {}
        memberships = memberships or []
        tips = ["time_to_repeat_procedure"]
        if account.get("favorite_services"):
            tips.append("related_service_upsell")
        if float(loyalty.get("points", loyalty.get("balance", 0)) or 0) > 0:
            tips.append("bonuses_expiring_soon")
        if any(int(m.get("visits_remaining", 99)) <= 2 for m in memberships):
            tips.append("renew_membership")
        tips.append("available_masters_today")
        tips.append("active_promos")
        return {
            "recommendations": tips,
            "ai_may_act": False,
            "proposes_only": True,
            "requires_client_confirmation": True,
            "advisor_ref": "ai_business_advisor",
            "marketing_ref": "ai_marketing_os",
        }
