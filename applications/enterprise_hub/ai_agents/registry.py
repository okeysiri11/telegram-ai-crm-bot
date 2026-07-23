"""AI Agent Registry — profiles, capabilities, permissions, lifecycle, versions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AgentRegistry:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.agent_types = list(DEFAULT_CONFIG.aa_agent_types)

    def register_agent(
        self,
        *,
        name: str,
        agent_type: str,
        capabilities: list[str] | None = None,
        permissions: list[str] | None = None,
        profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        at = agent_type.lower().strip()
        if at not in self.agent_types:
            raise ValidationError(f"agent_type must be one of {self.agent_types}")
        if not name:
            raise ValidationError("name required")
        aid = _id("aa_agent")
        return self.store.aa_agents.save(
            aid,
            {
                "agent_id": aid,
                "name": name,
                "agent_type": at,
                "capabilities": capabilities or [],
                "permissions": permissions or [],
                "profile": profile or {},
                "lifecycle": "registered",
                "version": 1,
                "at": _now(),
            },
        )

    def register_capability(self, *, name: str, description: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("name required")
        cid = _id("aa_cap")
        return self.store.aa_capabilities.save(
            cid,
            {
                "capability_id": cid,
                "name": name,
                "description": description,
                "at": _now(),
            },
        )

    def register_permission(self, *, name: str, scope: str = "enterprise") -> dict[str, Any]:
        if not name:
            raise ValidationError("name required")
        pid = _id("aa_perm")
        return self.store.aa_permissions.save(
            pid,
            {
                "permission_id": pid,
                "name": name,
                "scope": scope,
                "at": _now(),
            },
        )

    def set_lifecycle(self, *, agent_id: str, lifecycle: str) -> dict[str, Any]:
        agent = self.store.aa_agents.get(agent_id)
        if agent is None:
            raise NotFoundError(f"agent not found: {agent_id}")
        allowed = ("registered", "active", "paused", "retired")
        lc = lifecycle.lower().strip()
        if lc not in allowed:
            raise ValidationError(f"lifecycle must be one of {list(allowed)}")
        agent["lifecycle"] = lc
        agent["at"] = _now()
        return self.store.aa_agents.save(agent_id, agent)

    def version_agent(self, *, agent_id: str, note: str = "") -> dict[str, Any]:
        agent = self.store.aa_agents.get(agent_id)
        if agent is None:
            raise NotFoundError(f"agent not found: {agent_id}")
        agent["version"] = int(agent.get("version", 1)) + 1
        agent["at"] = _now()
        self.store.aa_agents.save(agent_id, agent)
        vid = _id("aa_ver")
        return self.store.aa_versions.save(
            vid,
            {
                "version_id": vid,
                "agent_id": agent_id,
                "version": agent["version"],
                "note": note,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "agents": self.store.aa_agents.count(),
            "capabilities": self.store.aa_capabilities.count(),
            "permissions": self.store.aa_permissions.count(),
            "versions": self.store.aa_versions.count(),
            "agent_types": self.agent_types,
        }
