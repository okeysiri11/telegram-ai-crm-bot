"""Enterprise AI roles (Sprint 12.5)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise.config import DEFAULT_CONFIG
from applications.enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise.shared.store import EnterpriseStore, enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class EnterpriseAI:
    def __init__(self, store: EnterpriseStore | None = None) -> None:
        self.store = store or enterprise_store
        self.roles = list(DEFAULT_CONFIG.ai_roles)

    def register(self, *, role: str, name: str = "", scope: str = "") -> dict[str, Any]:
        if role not in self.roles:
            raise ValidationError(f"role must be one of {self.roles}")
        aid = _id("eai")
        agent = {
            "agent_id": aid,
            "role": role,
            "name": name or f"{role}_ai",
            "scope": scope,
            "status": "ready",
            "registered_at": _now(),
        }
        return self.store.ai_agents.save(aid, agent)

    def invoke(self, *, agent_id: str, prompt: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        agent = self.store.ai_agents.get(agent_id)
        if agent is None:
            raise NotFoundError("ai_agent", agent_id)
        return {
            "agent_id": agent_id,
            "role": agent["role"],
            "prompt": prompt,
            "context": context or {},
            "response": f"[{agent['role']}] processed: {prompt[:120]}",
            "status": "completed",
            "at": _now(),
        }

    def list_agents(self, role: str | None = None) -> list[dict[str, Any]]:
        agents = self.store.ai_agents.list_all()
        if role:
            return [a for a in agents if a.get("role") == role]
        return agents

    def ensure_suite(self) -> list[dict[str, Any]]:
        existing = {a["role"] for a in self.store.ai_agents.list_all()}
        created = []
        for role in self.roles:
            if role not in existing:
                created.append(self.register(role=role, name=f"{role}_ai", scope="enterprise"))
        return created

    def status(self) -> dict[str, Any]:
        return {
            "agents": len(self.store.ai_agents.list_all()),
            "roles": self.roles,
            "by_role": {r: len(self.list_agents(r)) for r in self.roles},
        }


enterprise_ai = EnterpriseAI()
