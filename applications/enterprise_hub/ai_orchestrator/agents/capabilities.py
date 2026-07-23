"""Agent capability catalog."""

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


class AgentCapabilities:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = AgentRegistry(self.store)

    def describe(self, *, agent_id: str) -> dict[str, Any]:
        agent = self.registry.get(agent_id)
        cid = _id("aop_cap")
        return self.store.aop_capabilities.save(
            cid,
            {
                "capability_id": cid,
                "agent_id": agent_id,
                "specialization": agent.get("specialization"),
                "supported_tasks": agent.get("supported_tasks", []),
                "model": agent.get("model"),
                "at": _now(),
            },
        )
