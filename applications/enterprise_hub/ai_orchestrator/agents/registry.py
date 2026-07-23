"""Agent registry — specialization, load, cost, performance."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.ai_orchestrator.models import AGENT_STATUSES
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AgentRegistry:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def register(
        self,
        *,
        name: str,
        specialization: str,
        tasks: list[str] | None = None,
        model: str = "gpt-enterprise",
        cost_per_task: float = 0.01,
    ) -> dict[str, Any]:
        if not name or not str(name).strip():
            raise ValidationError("name is required")
        if not specialization:
            raise ValidationError("specialization is required")
        aid = _id("aop_agt")
        return self.store.aop_agents.save(
            aid,
            {
                "agent_id": aid,
                "name": name.strip(),
                "specialization": specialization.strip(),
                "supported_tasks": tasks or [specialization],
                "model": model,
                "status": "ready",
                "load": 0,
                "performance": 1.0,
                "cost_per_task": float(cost_per_task),
                "registered_at": _now(),
            },
        )

    def get(self, agent_id: str) -> dict[str, Any]:
        item = self.store.aop_agents.get(agent_id)
        if not item:
            raise NotFoundError(f"agent not found: {agent_id}")
        return item

    def set_status(self, *, agent_id: str, status: str, load: int | None = None) -> dict[str, Any]:
        agent = self.get(agent_id)
        st = status.lower().strip()
        if st not in AGENT_STATUSES:
            raise ValidationError(f"status must be one of {list(AGENT_STATUSES)}")
        agent["status"] = st
        if load is not None:
            agent["load"] = int(load)
        return self.store.aop_agents.save(agent_id, agent)

    def list_ready(self, *, specialization: str | None = None) -> list[dict[str, Any]]:
        out = []
        for a in self.store.aop_agents.list_all():
            if a.get("status") not in ("ready", "idle", "busy"):
                continue
            if specialization and specialization not in (a.get("specialization"), *(a.get("supported_tasks") or [])):
                continue
            out.append(a)
        return sorted(out, key=lambda x: (x.get("load", 0), x.get("cost_per_task", 0)))

    def status(self) -> dict[str, Any]:
        return {"agents": self.store.aop_agents.count(), "statuses": list(AGENT_STATUSES)}
