"""Tool registry — catalog of tools with permissions, cost, limits."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.ai_tools.models import PERMISSIONS, TOOL_DOMAINS, TOOL_STATUSES
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ToolRegistry:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def register(
        self,
        *,
        name: str,
        domain: str,
        description: str = "",
        owner: str = "platform",
        version: str = "1.0",
        permissions: list[str] | None = None,
        cost_per_call: float = 0.01,
        limits: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not name or not str(name).strip():
            raise ValidationError("name is required")
        dom = domain.lower().strip()
        if dom not in TOOL_DOMAINS:
            raise ValidationError(f"domain must be one of {list(TOOL_DOMAINS)}")
        perms = permissions or ["read", "execute"]
        for p in perms:
            if p not in PERMISSIONS:
                raise ValidationError(f"permission must be one of {list(PERMISSIONS)}")
        tid = _id("ats_tool")
        return self.store.ats_tools.save(
            tid,
            {
                "tool_id": tid,
                "name": name.strip(),
                "domain": dom,
                "version": version,
                "owner": owner,
                "description": description,
                "permissions": perms,
                "cost_per_call": float(cost_per_call),
                "limits": limits or {"timeout_ms": 5000, "max_calls_per_min": 60},
                "status": "active",
                "usage_count": 0,
                "registered_at": _now(),
            },
        )

    def get(self, tool_id: str) -> dict[str, Any]:
        item = self.store.ats_tools.get(tool_id)
        if not item:
            raise NotFoundError(f"tool not found: {tool_id}")
        return item

    def set_status(self, *, tool_id: str, status: str) -> dict[str, Any]:
        tool = self.get(tool_id)
        st = status.lower().strip()
        if st not in TOOL_STATUSES:
            raise ValidationError(f"status must be one of {list(TOOL_STATUSES)}")
        tool["status"] = st
        return self.store.ats_tools.save(tool_id, tool)

    def list_active(self, *, domain: str | None = None) -> list[dict[str, Any]]:
        out = []
        for t in self.store.ats_tools.list_all():
            if t.get("status") != "active":
                continue
            if domain and t.get("domain") != domain:
                continue
            out.append(t)
        return out

    def bump_usage(self, tool_id: str) -> dict[str, Any]:
        tool = self.get(tool_id)
        tool["usage_count"] = int(tool.get("usage_count", 0)) + 1
        return self.store.ats_tools.save(tool_id, tool)

    def status(self) -> dict[str, Any]:
        return {"tools": self.store.ats_tools.count(), "domains": list(TOOL_DOMAINS)}
