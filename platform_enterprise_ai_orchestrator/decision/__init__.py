"""Decision Engine — Sprint 24.0."""

from __future__ import annotations

from typing import Any


class DecisionEngine:
    def compose(
        self,
        *,
        problem: str,
        analysis: str,
        opinions: list[dict[str, Any]],
        contradictions: list[dict[str, Any]] | None = None,
        risks: list[str] | None = None,
        benefits: list[str] | None = None,
        forecast: str = "",
        action_plan: list[str] | None = None,
    ) -> dict[str, Any]:
        if not problem:
            raise ValueError("problem is required")
        opinions = list(opinions or [])
        agreement = [o for o in opinions if o.get("stance") == "support"]
        disagreement = [o for o in opinions if o.get("stance") != "support"]
        return {
            "problem": problem,
            "analysis": analysis or "council_analysis",
            "ai_opinions": opinions,
            "agreement_points": [o.get("summary") for o in agreement],
            "disagreement_points": [o.get("summary") for o in disagreement],
            "contradictions": list(contradictions or []),
            "risks": list(risks or ["execution_risk"]),
            "benefits": list(benefits or ["unified_ai_governance"]),
            "outcome_forecast": forecast or "positive_with_owner_oversight",
            "recommended_action_plan": list(action_plan or ["review_report", "owner_decide"]),
            "explained": True,
            "ai_may_act": False,
            "requires_owner_approval": True,
        }
