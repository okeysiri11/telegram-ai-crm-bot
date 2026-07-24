"""AI Context Builder — Sprint 24.2."""

from __future__ import annotations

from typing import Any


class AIContextBuilder:
    def build(
        self,
        *,
        context: dict[str, Any],
        entities: list[dict[str, Any]] | None = None,
        decisions: list[dict[str, Any]] | None = None,
        recommendations: list[dict[str, Any]] | None = None,
        outcomes: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        entities = [e for e in (entities or []) if e.get("ai_allowed", True) and not e.get("archived")]
        return {
            "relevant_entities": entities,
            "related_objects": list(context.get("related_objects") or []),
            "decision_history": list(decisions or []),
            "prior_recommendations": list(recommendations or []),
            "implementation_outcomes": list(outcomes or []),
            "filtered_for_ai": True,
            "ai_may_act": False,
        }
