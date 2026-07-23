"""Migration engine — org moves, merges, workspace export/import."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.tenancy.tenant_registry import TenantRegistry


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class MigrationEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.tenants = TenantRegistry(self.store)

    def export_workspace(self, *, workspace_id: str) -> dict[str, Any]:
        ws = self.store.tn_workspaces.get(workspace_id)
        if not ws:
            raise NotFoundError(f"workspace not found: {workspace_id}")
        eid = _id("tn_exp")
        return self.store.tn_exports.save(
            eid,
            {
                "export_id": eid,
                "workspace_id": workspace_id,
                "tenant_id": ws["tenant_id"],
                "payload": dict(ws),
                "at": _now(),
            },
        )

    def import_workspace(self, *, tenant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.tenants.get(tenant_id)
        if not isinstance(payload, dict) or not payload.get("name"):
            raise ValidationError("payload with name is required")
        wid = _id("tn_ws")
        record = {
            "workspace_id": wid,
            "tenant_id": tenant_id,
            "name": payload["name"],
            "kind": payload.get("kind", "custom"),
            "status": "active",
            "settings": payload.get("settings") or {},
            "imported": True,
            "created_at": _now(),
        }
        return self.store.tn_workspaces.save(wid, record)

    def merge_organizations(self, *, tenant_id: str, source_org_id: str, target_org_id: str) -> dict[str, Any]:
        self.tenants.get(tenant_id)
        source = self.store.tn_org_nodes.get(source_org_id)
        target = self.store.tn_org_nodes.get(target_org_id)
        if not source or not target:
            raise NotFoundError("source or target org not found")
        if source.get("tenant_id") != tenant_id or target.get("tenant_id") != tenant_id:
            raise ValidationError("orgs must belong to tenant")
        for node in self.store.tn_org_nodes.list_all():
            if node.get("parent_id") == source_org_id:
                node["parent_id"] = target_org_id
                self.store.tn_org_nodes.save(node["org_id"], node)
        mid = _id("tn_mig")
        return self.store.tn_migrations.save(
            mid,
            {
                "migration_id": mid,
                "tenant_id": tenant_id,
                "action": "merge",
                "source_org_id": source_org_id,
                "target_org_id": target_org_id,
                "at": _now(),
            },
        )

    def move_organization(
        self, *, tenant_id: str, org_id: str, new_parent_id: str | None
    ) -> dict[str, Any]:
        self.tenants.get(tenant_id)
        node = self.store.tn_org_nodes.get(org_id)
        if not node or node.get("tenant_id") != tenant_id:
            raise NotFoundError(f"org not found: {org_id}")
        if new_parent_id:
            parent = self.store.tn_org_nodes.get(new_parent_id)
            if not parent or parent.get("tenant_id") != tenant_id:
                raise NotFoundError(f"parent not found: {new_parent_id}")
        node["parent_id"] = new_parent_id
        self.store.tn_org_nodes.save(org_id, node)
        mid = _id("tn_mig")
        return self.store.tn_migrations.save(
            mid,
            {
                "migration_id": mid,
                "tenant_id": tenant_id,
                "action": "move",
                "org_id": org_id,
                "new_parent_id": new_parent_id,
                "at": _now(),
            },
        )
