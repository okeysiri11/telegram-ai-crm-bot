"""Policy engine — agent/tool permissions, roles, cost, confirmations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ToolPolicyEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def define(
        self,
        *,
        name: str,
        allowed_agents: list[str] | None = None,
        allowed_roles: list[str] | None = None,
        allowed_domains: list[str] | None = None,
        max_cost: float = 10.0,
        require_confirmation: bool = False,
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("name is required")
        pid = _id("ats_pol")
        return self.store.ats_policies.save(
            pid,
            {
                "policy_id": pid,
                "name": name.strip(),
                "allowed_agents": allowed_agents or ["*"],
                "allowed_roles": allowed_roles or ["admin", "agent", "operator"],
                "allowed_domains": allowed_domains or ["*"],
                "max_cost": float(max_cost),
                "require_confirmation": require_confirmation,
                "active": True,
                "at": _now(),
            },
        )

    def authorize(
        self,
        *,
        agent_id: str,
        role: str,
        domain: str,
        cost: float,
        confirmed: bool = False,
    ) -> dict[str, Any]:
        policies = [p for p in self.store.ats_policies.list_all() if p.get("active")]
        if not policies:
            return {"allowed": True, "notes": ["no policies"], "require_confirmation": False}
        allowed = False
        require_confirmation = False
        notes = []
        for p in policies:
            agents = p.get("allowed_agents") or []
            roles = p.get("allowed_roles") or []
            domains = p.get("allowed_domains") or []
            agent_ok = "*" in agents or agent_id in agents
            role_ok = role in roles
            domain_ok = "*" in domains or domain in domains
            cost_ok = float(cost) <= float(p.get("max_cost", 10))
            if agent_ok and role_ok and domain_ok and cost_ok:
                allowed = True
                if p.get("require_confirmation"):
                    require_confirmation = True
            else:
                notes.append(f"missed {p['name']}")
        if require_confirmation and not confirmed:
            allowed = False
            notes.append("user confirmation required")
        eid = _id("ats_auth")
        return self.store.ats_authz.save(
            eid,
            {
                "authz_id": eid,
                "agent_id": agent_id,
                "role": role,
                "domain": domain,
                "cost": cost,
                "allowed": allowed,
                "require_confirmation": require_confirmation,
                "notes": notes,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"policies": self.store.ats_policies.count()}
