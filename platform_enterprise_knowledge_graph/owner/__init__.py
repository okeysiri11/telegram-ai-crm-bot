"""Owner Control over knowledge — Sprint 24.2."""

from __future__ import annotations

from typing import Any


class OwnerKnowledgeControl:
    ACTIONS = ("view_links", "edit_link", "confirm_knowledge", "archive_knowledge", "forbid_ai_use")

    def act(self, *, action: str, actor: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        action = (action or "").lower()
        if action not in self.ACTIONS:
            raise ValueError(f"unsupported owner action: {action}")
        if actor != "platform_owner":
            raise ValueError("only platform_owner may control knowledge")
        return {
            "action": action,
            "actor": actor,
            "payload": dict(payload or {}),
            "approved": True,
            "ai_may_act": False,
        }
