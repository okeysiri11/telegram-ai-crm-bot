"""Organization hierarchy manager — holding → employee."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.tenancy.models import ORG_LEVELS
from applications.enterprise_hub.tenancy.tenant_registry import TenantRegistry


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class OrganizationManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.tenants = TenantRegistry(self.store)

    def create_node(
        self,
        *,
        tenant_id: str,
        name: str,
        level: str,
        parent_id: str | None = None,
        code: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.tenants.get(tenant_id)
        if not name or not str(name).strip():
            raise ValidationError("name is required")
        lv = level.lower().strip()
        if lv not in ORG_LEVELS:
            raise ValidationError(f"level must be one of {list(ORG_LEVELS)}")
        if parent_id:
            parent = self.store.tn_org_nodes.get(parent_id)
            if not parent:
                raise NotFoundError(f"parent not found: {parent_id}")
            if parent.get("tenant_id") != tenant_id:
                raise ValidationError("parent must belong to same tenant")
        oid = _id("tn_org")
        return self.store.tn_org_nodes.save(
            oid,
            {
                "org_id": oid,
                "tenant_id": tenant_id,
                "name": name.strip(),
                "level": lv,
                "parent_id": parent_id,
                "code": (code or name).lower().replace(" ", "-")[:48],
                "meta": meta or {},
                "created_at": _now(),
            },
        )

    def hierarchy(self, *, tenant_id: str) -> dict[str, Any]:
        self.tenants.get(tenant_id)
        nodes = [n for n in self.store.tn_org_nodes.list_all() if n.get("tenant_id") == tenant_id]
        by_parent: dict[str | None, list[dict[str, Any]]] = {}
        for n in nodes:
            by_parent.setdefault(n.get("parent_id"), []).append(n)

        def _tree(parent: str | None) -> list[dict[str, Any]]:
            out = []
            for n in by_parent.get(parent, []):
                out.append({**n, "children": _tree(n["org_id"])})
            return out

        return {"tenant_id": tenant_id, "roots": _tree(None), "count": len(nodes)}

    def get(self, org_id: str) -> dict[str, Any]:
        item = self.store.tn_org_nodes.get(org_id)
        if not item:
            raise NotFoundError(f"org node not found: {org_id}")
        return item

    def status(self) -> dict[str, Any]:
        return {"org_nodes": self.store.tn_org_nodes.count(), "levels": list(ORG_LEVELS)}
