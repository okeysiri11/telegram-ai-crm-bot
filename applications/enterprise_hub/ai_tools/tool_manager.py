"""Tool manager — high-level catalog operations."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.ai_tools.tool_registry import ToolRegistry
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class ToolManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = ToolRegistry(self.store)

    def register(self, **kwargs: Any) -> dict[str, Any]:
        return self.registry.register(**kwargs)

    def disable(self, *, tool_id: str) -> dict[str, Any]:
        return self.registry.set_status(tool_id=tool_id, status="disabled")

    def enable(self, *, tool_id: str) -> dict[str, Any]:
        return self.registry.set_status(tool_id=tool_id, status="active")

    def catalog(self) -> list[dict[str, Any]]:
        return self.registry.list_active()

    def status(self) -> dict[str, Any]:
        return self.registry.status()
