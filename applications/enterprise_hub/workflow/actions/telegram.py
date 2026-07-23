"""Telegram workflow action."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.workflow.actions import run_action


class TelegramAction:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def run(self, *, target: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return run_action(self.store, action_type="telegram", target=target, payload=payload)
