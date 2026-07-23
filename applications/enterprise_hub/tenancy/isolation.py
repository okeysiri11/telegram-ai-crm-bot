"""Tenant isolation — data, files, AI context, API, queues, logs, backups."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.tenancy.models import ISOLATION_SCOPES
from applications.enterprise_hub.tenancy.tenant_registry import TenantRegistry


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class IsolationEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.tenants = TenantRegistry(self.store)

    def enforce(self, *, tenant_id: str, scope: str, resource_key: str) -> dict[str, Any]:
        self.tenants.get(tenant_id)
        sc = scope.lower().strip()
        if sc not in ISOLATION_SCOPES:
            raise ValidationError(f"scope must be one of {list(ISOLATION_SCOPES)}")
        if not resource_key:
            raise ValidationError("resource_key is required")
        iid = _id("tn_iso")
        boundary = f"tenant:{tenant_id}:{sc}:{resource_key}"
        return self.store.tn_isolation.save(
            iid,
            {
                "isolation_id": iid,
                "tenant_id": tenant_id,
                "scope": sc,
                "resource_key": resource_key,
                "boundary": boundary,
                "enforced": True,
                "at": _now(),
            },
        )

    def context_key(self, *, tenant_id: str, scope: str = "ai_context") -> str:
        self.tenants.get(tenant_id)
        return f"ctx:{tenant_id}:{scope}"

    def status(self) -> dict[str, Any]:
        return {"boundaries": self.store.tn_isolation.count(), "scopes": list(ISOLATION_SCOPES)}
