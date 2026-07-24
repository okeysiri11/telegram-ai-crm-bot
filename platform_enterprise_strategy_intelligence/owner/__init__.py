"""Owner Decision Center for strategy — Sprint 24.7."""

from __future__ import annotations

from typing import Any

from platform_enterprise_strategy_intelligence.models import OWNER_ACTIONS


class OwnerStrategyDecision:
    def decide(
        self,
        *,
        action: str,
        actor: str,
        strategy_id: str,
        modifications: dict[str, Any] | None = None,
        notes: str = "",
    ) -> dict[str, Any]:
        action = (action or "").lower()
        if action not in OWNER_ACTIONS:
            raise ValueError(f"unsupported action: {action}")
        if actor != "platform_owner":
            raise ValueError("only platform_owner may decide")
        if not strategy_id:
            raise ValueError("strategy_id is required")
        status = {"approve": "approved", "reject": "rejected", "modify": "modified"}[action]
        return {
            "strategy_id": strategy_id,
            "action": action,
            "actor": actor,
            "status": status,
            "modifications": dict(modifications or {}) if action == "modify" else None,
            "notes": notes or None,
            "execution_workflow": action == "approve",
            "ai_may_act": False,
            "autonomous_decide": False,
        }
