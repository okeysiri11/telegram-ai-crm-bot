"""Workspace manager — per-tenant CRM/ERP/AI/custom spaces."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.tenancy.models import WORKSPACE_KINDS
from applications.enterprise_hub.tenancy.tenant_registry import TenantRegistry


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class WorkspaceManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.tenants = TenantRegistry(self.store)

    def create(
        self,
        *,
        tenant_id: str,
        name: str,
        kind: str = "crm",
        settings: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.tenants.get(tenant_id)
        if not name or not str(name).strip():
            raise ValidationError("name is required")
        k = kind.lower().strip()
        if k not in WORKSPACE_KINDS:
            raise ValidationError(f"kind must be one of {list(WORKSPACE_KINDS)}")
        wid = _id("tn_ws")
        return self.store.tn_workspaces.save(
            wid,
            {
                "workspace_id": wid,
                "tenant_id": tenant_id,
                "name": name.strip(),
                "kind": k,
                "status": "active",
                "settings": settings or {},
                "created_at": _now(),
            },
        )

    def get(self, workspace_id: str) -> dict[str, Any]:
        item = self.store.tn_workspaces.get(workspace_id)
        if not item:
            raise NotFoundError(f"workspace not found: {workspace_id}")
        return item

    def list_for_tenant(self, tenant_id: str) -> list[dict[str, Any]]:
        self.tenants.get(tenant_id)
        return [w for w in self.store.tn_workspaces.list_all() if w.get("tenant_id") == tenant_id]

    def status(self) -> dict[str, Any]:
        return {"workspaces": self.store.tn_workspaces.count(), "kinds": list(WORKSPACE_KINDS)}
