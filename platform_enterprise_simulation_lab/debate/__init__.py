"""AI Debate Mode — Sprint 24.4."""

from __future__ import annotations

from typing import Any


class AIDebateMode:
    COUNCIL_ROLES = (
        "product",
        "technical",
        "business",
        "finance",
        "marketing",
        "commerce",
        "security",
        "ux",
    )

    def debate(self, *, scenario_name: str, impacts: dict[str, Any] | None = None) -> dict[str, Any]:
        impacts = dict(impacts or {})
        opinions = []
        for role in self.COUNCIL_ROLES:
            stance = "support"
            if role in ("finance", "security") and float(impacts.get("risks", 0)) >= 0.25:
                stance = "caution"
            elif role in ("marketing", "commerce") and float(impacts.get("revenue", 0)) > 0:
                stance = "accelerate"
            opinions.append(
                {
                    "role": role,
                    "stance": stance,
                    "summary": f"{role} view on {scenario_name}",
                }
            )
        return {
            "scenario": scenario_name,
            "opinions": opinions,
            "unified_report": True,
            "via_multi_agent_council": True,
            "ai_may_act": False,
            "requires_owner": True,
        }
