"""Owner / trust-policy gate for learning — Sprint 24.8."""

from __future__ import annotations

from typing import Any

from platform_enterprise_learning_engine.models import OWNER_ACTIONS


class OwnerLearningDecision:
    def decide(
        self,
        *,
        action: str,
        actor: str,
        learning_id: str,
        notes: str = "",
    ) -> dict[str, Any]:
        action = (action or "").lower()
        if action not in OWNER_ACTIONS:
            raise ValueError(f"unsupported action: {action}")
        if actor not in ("platform_owner", "trust_policy"):
            raise ValueError("only platform_owner or trust_policy may confirm knowledge")
        if action == "policy_trust" and actor != "trust_policy":
            raise ValueError("policy_trust requires trust_policy actor")
        if action in ("approve", "reject") and actor != "platform_owner":
            raise ValueError("approve/reject require platform_owner")
        if not learning_id:
            raise ValueError("learning_id is required")
        status = {
            "approve": "approved",
            "reject": "rejected",
            "policy_trust": "policy_trusted",
        }[action]
        return {
            "learning_id": learning_id,
            "action": action,
            "actor": actor,
            "status": status,
            "notes": notes or None,
            "ai_may_act": False,
            "autonomous_learn": False,
            "may_change_algorithms": False,
        }
