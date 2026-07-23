"""Agent lifecycle — start, stop, recycle."""

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


class AgentLifecycle:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = AgentRegistry(self.store)

    def start(self, *, agent_id: str) -> dict[str, Any]:
        agent = self.registry.set_status(agent_id=agent_id, status="ready", load=0)
        lid = _id("aop_lc")
        return self.store.aop_lifecycle.save(
            lid,
            {"lifecycle_id": lid, "agent_id": agent_id, "action": "start", "agent": agent, "at": _now()},
        )

    def stop(self, *, agent_id: str) -> dict[str, Any]:
        agent = self.registry.set_status(agent_id=agent_id, status="offline", load=0)
        lid = _id("aop_lc")
        return self.store.aop_lifecycle.save(
            lid,
            {"lifecycle_id": lid, "agent_id": agent_id, "action": "stop", "agent": agent, "at": _now()},
        )

    def recycle(self, *, agent_id: str) -> dict[str, Any]:
        self.stop(agent_id=agent_id)
        return self.start(agent_id=agent_id)
