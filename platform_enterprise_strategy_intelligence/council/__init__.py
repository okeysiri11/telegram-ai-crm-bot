"""AI Strategic Council — Sprint 24.7."""

from __future__ import annotations

from typing import Any

from platform_enterprise_strategy_intelligence.models import COUNCIL_ROLES


class AIStrategicCouncil:
    def review(self, *, strategy: dict[str, Any], risk_score: float = 0.3) -> dict[str, Any]:
        opinions = []
        for role in COUNCIL_ROLES:
            stance = "support"
            if role in ("finance", "security", "legal") and risk_score >= 0.5:
                stance = "caution"
            elif role in ("business", "marketing", "product") and strategy.get("goal"):
                stance = "accelerate"
            elif role == "analytics":
                stance = "data_backed"
            opinions.append({
                "role": role,
                "stance": stance,
                "independent": True,
                "summary": f"{role} on {strategy.get('name')}",
            })
        return {
            "strategy_id": strategy.get("strategy_id"),
            "opinions": opinions,
            "unified": True,
            "via_multi_agent_council": True,
            "ai_may_act": False,
            "requires_owner": True,
            "pipeline": [
                "strategy_intelligence",
                "multi_agent_council",
                "owner_approval",
                "execution_workflow",
            ],
        }
