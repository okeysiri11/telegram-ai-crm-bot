"""AI Approval Workflow — Sprint 22.5."""

from __future__ import annotations

from typing import Any

from platform_ai_marketing_os.models import APPROVAL_ACTIONS


class AIApprovalWorkflow:
    def create_card(
        self,
        *,
        reason: str,
        expected_effect: dict[str, Any],
        reach_forecast: int = 1000,
        load_forecast: float = 0.1,
        budget: float = 0.0,
        models_used: list[str] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "reason": reason,
            "expected_effect": expected_effect,
            "reach_forecast": reach_forecast,
            "load_forecast": load_forecast,
            "budget": budget,
            "models_used": list(models_used or ["text-gen", "image-gen"]),
            "payload": dict(payload or {}),
            "status": "pending_owner",
            "ai_published": False,
            "available_actions": list(APPROVAL_ACTIONS),
        }

    def decide(self, card: dict[str, Any], *, action: str, owner_id: str, edits: dict[str, Any] | None = None) -> dict[str, Any]:
        if not owner_id:
            raise ValueError("owner_id is required")
        if action not in APPROVAL_ACTIONS:
            raise ValueError(f"invalid approval action: {action}")
        updated = dict(card)
        updated["owner_id"] = owner_id.strip()
        updated["action"] = action
        updated["edits"] = dict(edits or {})
        updated["ai_published"] = False
        if action == "approve":
            updated["status"] = "approved"
            updated["publish_allowed"] = True
        elif action == "schedule":
            updated["status"] = "scheduled"
            updated["publish_allowed"] = True
        elif action == "edit":
            updated["status"] = "edited_pending"
            updated["publish_allowed"] = False
            if edits:
                updated["payload"] = {**updated.get("payload", {}), **edits}
        else:
            updated["status"] = "rejected"
            updated["publish_allowed"] = False
        return updated
