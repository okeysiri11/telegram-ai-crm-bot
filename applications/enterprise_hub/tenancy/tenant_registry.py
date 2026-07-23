"""Tenant registry — Sprint 20.0."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.tenancy.models import ENVIRONMENTS, LICENSE_TIERS


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class TenantRegistry:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def register(
        self,
        *,
        name: str,
        slug: str | None = None,
        license_tier: str = "business",
        environment: str = "production",
    ) -> dict[str, Any]:
        if not name or not str(name).strip():
            raise ValidationError("name is required")
        tier = license_tier.lower().strip()
        if tier not in LICENSE_TIERS:
            raise ValidationError(f"license_tier must be one of {list(LICENSE_TIERS)}")
        env = environment.lower().strip()
        if env not in ENVIRONMENTS:
            raise ValidationError(f"environment must be one of {list(ENVIRONMENTS)}")
        tid = _id("tn")
        code = (slug or name).lower().replace(" ", "-")[:48]
        return self.store.tn_tenants.save(
            tid,
            {
                "tenant_id": tid,
                "name": name.strip(),
                "slug": code,
                "license_tier": tier,
                "environment": env,
                "status": "active",
                "created_at": _now(),
            },
        )

    def get(self, tenant_id: str) -> dict[str, Any]:
        item = self.store.tn_tenants.get(tenant_id)
        if not item:
            raise NotFoundError(f"tenant not found: {tenant_id}")
        return item

    def list_tenants(self) -> list[dict[str, Any]]:
        return self.store.tn_tenants.list_all()

    def status(self) -> dict[str, Any]:
        return {"tenants": self.store.tn_tenants.count(), "tiers": list(LICENSE_TIERS)}
