"""Quick actions — Sprint 22.3."""

from __future__ import annotations

from typing import Any

from platform_beauty_workspace.models import QUICK_ACTIONS


class QuickActions:
    def actions(self) -> list[str]:
        return list(QUICK_ACTIONS)

    def run(self, *, action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if action not in QUICK_ACTIONS:
            raise ValueError(f"unknown quick action: {action}")
        payload = payload or {}
        return {
            "action": action,
            "payload": payload,
            "max_seconds": 30 if action == "book_in_30s" else 60,
            "delegates_to": "beauty_os",
            "clicks": 1 if action in ("book_in_30s", "repeat_last_visit") else 2,
            "ai_executed": False,
            "status": "ready",
        }
