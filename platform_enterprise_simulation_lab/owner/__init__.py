"""Owner Decision Center (simulation) — Sprint 24.4."""

from __future__ import annotations

from typing import Any


class OwnerSimulationDecision:
    ACTIONS = ("approve", "approve_with_changes", "request_alternative", "reject", "simulate_again")

    def decide(self, *, action: str, actor: str, scenario_id: str, notes: str = "") -> dict[str, Any]:
        action = (action or "").lower()
        if action not in self.ACTIONS:
            raise ValueError(f"unsupported action: {action}")
        if actor != "platform_owner":
            raise ValueError("only platform_owner may decide")
        if not scenario_id:
            raise ValueError("scenario_id is required")
        return {
            "scenario_id": scenario_id,
            "action": action,
            "actor": actor,
            "notes": notes or None,
            "approved": action in ("approve", "approve_with_changes"),
            "deployed": False,
            "ai_may_act": False,
            "requires_owner": True,
        }
