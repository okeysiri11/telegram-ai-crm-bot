"""Owner Command Center — Sprint 23.0."""

from __future__ import annotations

from typing import Any

from platform_enterprise_operations.models import OWNER_ACTIONS


class OwnerCommandCenter:
    def approve(self, *, action: str, actor: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        action = (action or "").lower()
        if action not in OWNER_ACTIONS:
            raise ValueError(f"unsupported owner action: {action}")
        if actor != "platform_owner":
            raise ValueError("only platform_owner may approve")
        return {
            "action": action,
            "actor": actor,
            "payload": dict(payload or {}),
            "approved": True,
            "expert_board_required": action in ("approve_release", "approve_global_change", "approve_ai_recommendation", "approve_mass_update"),
            "ai_may_act": False,
        }
