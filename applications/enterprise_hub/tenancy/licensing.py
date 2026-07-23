"""License manager — Free → Custom tiers."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.tenancy.models import LICENSE_TIERS
from applications.enterprise_hub.tenancy.tenant_registry import TenantRegistry


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


TIER_LIMITS = {
    "free": {"users": 5, "workspaces": 1, "ai_tokens": 10_000},
    "startup": {"users": 25, "workspaces": 3, "ai_tokens": 100_000},
    "business": {"users": 200, "workspaces": 10, "ai_tokens": 1_000_000},
    "enterprise": {"users": 5_000, "workspaces": 100, "ai_tokens": 50_000_000},
    "government": {"users": 10_000, "workspaces": 200, "ai_tokens": 100_000_000},
    "custom": {"users": -1, "workspaces": -1, "ai_tokens": -1},
}


class LicenseManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.tenants = TenantRegistry(self.store)

    def assign(self, *, tenant_id: str, tier: str, seats: int | None = None) -> dict[str, Any]:
        self.tenants.get(tenant_id)
        t = tier.lower().strip()
        if t not in LICENSE_TIERS:
            raise ValidationError(f"tier must be one of {list(LICENSE_TIERS)}")
        lid = _id("tn_lic")
        limits = dict(TIER_LIMITS[t])
        if seats is not None:
            limits["users"] = int(seats)
        return self.store.tn_licenses.save(
            lid,
            {
                "license_id": lid,
                "tenant_id": tenant_id,
                "tier": t,
                "limits": limits,
                "status": "active",
                "assigned_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"licenses": self.store.tn_licenses.count(), "tiers": list(LICENSE_TIERS)}
