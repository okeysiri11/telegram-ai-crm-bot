# Tenant service — multi-tenant isolation.

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ecosystem.shared.exceptions import NotFoundError
from ecosystem.shared.store import EcosystemStore, ecosystem_store


def _id() -> str:
    return str(uuid.uuid4())


def _ts() -> float:
    return time.time()


@dataclass
class Tenant:
    tenant_id: str = field(default_factory=_id)
    name: str = ""
    slug: str = ""
    plan: str = "standard"
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "slug": self.slug,
            "plan": self.plan,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


class TenantService:
    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store

    def create(self, name: str, *, slug: str = "", plan: str = "standard") -> Tenant:
        tenant = Tenant(name=name, slug=slug or name.lower().replace(" ", "-"), plan=plan)
        self._store.tenants.save(tenant.tenant_id, tenant)
        return tenant

    def get(self, tenant_id: str) -> Tenant:
        tenant = self._store.tenants.get(tenant_id)
        if tenant is None:
            raise NotFoundError("Tenant", tenant_id)
        return tenant

    def list_all(self) -> list[Tenant]:
        return self._store.tenants.list_all()


tenant_service = TenantService()
