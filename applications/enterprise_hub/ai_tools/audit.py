"""Audit log for tool/skill executions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ToolAudit:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def log(
        self,
        *,
        event: str,
        tool_id: str | None = None,
        skill_id: str | None = None,
        agent_id: str = "system",
        permissions: list[str] | None = None,
        detail: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        aid = _id("ats_aud")
        return self.store.ats_audit.save(
            aid,
            {
                "audit_id": aid,
                "event": event,
                "tool_id": tool_id,
                "skill_id": skill_id,
                "agent_id": agent_id,
                "permissions": permissions or [],
                "detail": detail or {},
                "error": error,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.ats_audit.count()}
