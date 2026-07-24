"""Owner Decision Center for optimization — Sprint 24.6."""

from __future__ import annotations

from typing import Any

from platform_enterprise_autonomous_optimization.models import OWNER_ACTIONS


class OwnerOptimizationDecision:
    def decide(self, *, action: str, actor: str, opportunity_id: str, modifications: dict[str, Any] | None = None, notes: str = "") -> dict[str, Any]:
        action = (action or "").lower()
        if action not in OWNER_ACTIONS:
            raise ValueError(f"unsupported action: {action}")
        if actor != "platform_owner":
            raise ValueError("only platform_owner may decide")
        if not opportunity_id:
            raise ValueError("opportunity_id is required")
        status = {"approve": "approved", "reject": "rejected", "modify": "modified"}[action]
        return {
            "opportunity_id": opportunity_id,
            "action": action,
            "actor": actor,
            "status": status,
            "modifications": dict(modifications or {}) if action == "modify" else None,
            "notes": notes or None,
            "implemented": False,
            "ai_may_act": False,
            "autonomous_deploy": False,
        }
