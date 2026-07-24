"""AI Assistant panel — Sprint 22.3."""

from __future__ import annotations

from typing import Any


class AIAssistantPanel:
    def render(
        self,
        *,
        open_slots: list[str] | None = None,
        recommendations: list[str] | None = None,
        warnings: list[str] | None = None,
        overloaded_masters: list[str] | None = None,
        churn_risks: list[str] | None = None,
        promo_ideas: list[str] | None = None,
    ) -> dict[str, Any]:
        return {
            "side": "right",
            "open_slots": list(open_slots or []),
            "recommendations": list(recommendations or []),
            "warnings": list(warnings or []),
            "overloaded_masters": list(overloaded_masters or []),
            "churn_risks": list(churn_risks or []),
            "promo_ideas": list(promo_ideas or []),
            "ai_may_execute": False,
            "proposes_only": True,
            "advisor_ref": "ai_business_advisor",
            "product_intelligence_ref": "product_intelligence",
        }
