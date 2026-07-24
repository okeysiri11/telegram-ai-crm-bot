"""Reception panel — Sprint 22.3."""

from __future__ import annotations

from typing import Any

from platform_beauty_workspace.models import RECEPTION_ACTIONS


class ReceptionPanel:
    def actions(self) -> list[str]:
        return list(RECEPTION_ACTIONS)

    def invoke(self, *, action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if action not in RECEPTION_ACTIONS:
            raise ValueError(f"unknown reception action: {action}")
        payload = payload or {}
        return {
            "action": action,
            "payload": payload,
            "delegates_to": "beauty_os",
            "clicks_budget": "1-3",
            "executed_by_ai": False,
            "status": "queued",
        }
