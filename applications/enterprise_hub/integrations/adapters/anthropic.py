"""anthropic adapter."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.integrations.adapters import invoke_adapter
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class AnthropicAdapter:
    name = "anthropic"

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def invoke(self, *, operation: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return invoke_adapter(
            self.store, adapter=self.name, operation=operation, payload=payload
        )
