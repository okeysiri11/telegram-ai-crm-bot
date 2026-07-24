"""Owner Decision Center — Sprint 24.0."""

from __future__ import annotations

from typing import Any

from platform_enterprise_ai_orchestrator.models import OWNER_ACTIONS


class OwnerDecisionCenter:
    def decide(self, *, action: str, actor: str, decision_id: str, changes: str = "", notes: str = "") -> dict[str, Any]:
        action = (action or "").lower()
        if action not in OWNER_ACTIONS:
            raise ValueError(f"unsupported owner action: {action}")
        if actor != "platform_owner":
            raise ValueError("only platform_owner may decide")
        if not decision_id:
            raise ValueError("decision_id is required")
        return {
            "decision_id": decision_id,
            "action": action,
            "actor": actor,
            "changes": changes or None,
            "notes": notes or None,
            "approved": action in ("approve", "approve_with_changes"),
            "ai_may_act": False,
            "critical_without_owner": False,
        }
