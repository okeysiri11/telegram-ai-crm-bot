"""Built-in communication tools."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.ai_tools.tool_registry import ToolRegistry
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class CommunicationTool:
    domain = "communication"

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.registry = ToolRegistry(store or enterprise_hub_store)

    def register(self, *, name: str, **kwargs: Any) -> dict[str, Any]:
        return self.registry.register(name=name, domain=self.domain, **kwargs)
