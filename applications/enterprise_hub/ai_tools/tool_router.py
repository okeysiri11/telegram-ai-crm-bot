"""Tool router — resolve tool by name/domain."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.ai_tools.tool_registry import ToolRegistry
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ToolRouter:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = ToolRegistry(self.store)

    def resolve(self, *, name: str | None = None, domain: str | None = None, tool_id: str | None = None) -> dict[str, Any]:
        if tool_id:
            tool = self.registry.get(tool_id)
        elif name:
            matches = [t for t in self.registry.list_active() if t.get("name") == name]
            if not matches:
                raise NotFoundError(f"tool not found by name: {name}")
            tool = matches[0]
        elif domain:
            matches = self.registry.list_active(domain=domain)
            if not matches:
                raise NotFoundError(f"no active tool in domain: {domain}")
            tool = matches[0]
        else:
            raise ValidationError("name, domain, or tool_id required")
        rid = _id("ats_rt")
        return self.store.ats_routes.save(
            rid,
            {"route_id": rid, "tool_id": tool["tool_id"], "name": tool["name"], "domain": tool["domain"], "at": _now()},
        )
