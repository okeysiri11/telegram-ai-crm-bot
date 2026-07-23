"""Tenant manager — tenants, workspaces, companies, orgs, environments."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.tenancy.models import ENVIRONMENTS
from applications.enterprise_hub.tenancy.tenant_registry import TenantRegistry


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class TenantManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = TenantRegistry(self.store)

    def create_tenant(self, **kwargs: Any) -> dict[str, Any]:
        return self.registry.register(**kwargs)

    def attach_environment(
        self, *, tenant_id: str, name: str, env_type: str = "production"
    ) -> dict[str, Any]:
        self.registry.get(tenant_id)
        et = env_type.lower().strip()
        if et not in ENVIRONMENTS:
            raise ValidationError(f"env_type must be one of {list(ENVIRONMENTS)}")
        eid = _id("tn_env")
        return self.store.tn_environments.save(
            eid,
            {
                "environment_id": eid,
                "tenant_id": tenant_id,
                "name": name.strip() or et,
                "env_type": et,
                "created_at": _now(),
            },
        )

    def analytics(self, *, tenant_id: str) -> dict[str, Any]:
        self.registry.get(tenant_id)
        workspaces = [w for w in self.store.tn_workspaces.list_all() if w.get("tenant_id") == tenant_id]
        orgs = [o for o in self.store.tn_org_nodes.list_all() if o.get("tenant_id") == tenant_id]
        usage = [u for u in self.store.tn_usage.list_all() if u.get("tenant_id") == tenant_id]
        aid = _id("tn_an")
        report = {
            "analytics_id": aid,
            "tenant_id": tenant_id,
            "resource_usage": {
                "workspaces": len(workspaces),
                "org_nodes": len(orgs),
                "usage_events": len(usage),
            },
            "ai_spend": sum(float(u.get("ai_cost", 0) or 0) for u in usage),
            "active_users": sum(int(u.get("active_users", 0) or 0) for u in usage),
            "module_stats": {
                w.get("kind"): w.get("status", "active") for w in workspaces if w.get("kind")
            },
            "at": _now(),
        }
        return self.store.tn_analytics.save(aid, report)

    def record_usage(
        self,
        *,
        tenant_id: str,
        active_users: int = 0,
        ai_cost: float = 0.0,
        module: str = "crm",
    ) -> dict[str, Any]:
        self.registry.get(tenant_id)
        uid = _id("tn_use")
        return self.store.tn_usage.save(
            uid,
            {
                "usage_id": uid,
                "tenant_id": tenant_id,
                "active_users": int(active_users),
                "ai_cost": float(ai_cost),
                "module": module,
                "at": _now(),
            },
        )

    def get(self, tenant_id: str) -> dict[str, Any]:
        return self.registry.get(tenant_id)

    def status(self) -> dict[str, Any]:
        return {
            "tenants": self.store.tn_tenants.count(),
            "environments": self.store.tn_environments.count(),
            "analytics": self.store.tn_analytics.count(),
            "usage": self.store.tn_usage.count(),
        }
