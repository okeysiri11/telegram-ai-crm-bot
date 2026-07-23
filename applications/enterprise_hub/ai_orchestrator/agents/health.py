"""Agent health checks."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.ai_orchestrator.agents.registry import AgentRegistry
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AgentHealth:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = AgentRegistry(self.store)

    def check(self, *, agent_id: str) -> dict[str, Any]:
        agent = self.registry.get(agent_id)
        healthy = agent.get("status") in ("ready", "idle", "busy")
        hid = _id("aop_hl")
        return self.store.aop_health.save(
            hid,
            {
                "health_id": hid,
                "agent_id": agent_id,
                "healthy": healthy,
                "status": agent.get("status"),
                "load": agent.get("load", 0),
                "at": _now(),
            },
        )
