"""Office organization entity (branch-level facility)."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.tenancy.organization_manager import OrganizationManager


class OfficeEntity:
    level = "branch"

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.orgs = OrganizationManager(store or enterprise_hub_store)

    def create(self, *, tenant_id: str, name: str, parent_id: str | None = None, **meta: Any) -> dict[str, Any]:
        payload = {"facility": "office", **(meta or {})}
        return self.orgs.create_node(
            tenant_id=tenant_id, name=name, level=self.level, parent_id=parent_id, meta=payload
        )
