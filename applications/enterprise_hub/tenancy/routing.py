"""Data routing — tenant-aware request/context routing."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.tenancy.tenant_registry import TenantRegistry


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class TenantRouter:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.tenants = TenantRegistry(self.store)

    def route(
        self,
        *,
        tenant_id: str,
        target: str,
        path: str = "/",
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        self.tenants.get(tenant_id)
        if not target or not str(target).strip():
            raise ValidationError("target is required")
        rid = _id("tn_rt")
        return self.store.tn_routes.save(
            rid,
            {
                "route_id": rid,
                "tenant_id": tenant_id,
                "workspace_id": workspace_id,
                "target": target.strip(),
                "path": path or "/",
                "resolved": f"/{tenant_id}/{target.strip()}{path or '/'}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"routes": self.store.tn_routes.count()}
