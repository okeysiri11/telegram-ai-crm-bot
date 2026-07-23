"""Integration Registry — catalog of external integrations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store
from applications.enterprise_hub.integrations.models import ADAPTERS, INTEGRATION_STATUSES, PROTOCOLS


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class IntegrationRegistry:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def register(
        self,
        *,
        name: str,
        protocol: str,
        adapter: str = "custom",
        version: str = "1.0",
        owner: str = "system",
        connection: dict[str, Any] | None = None,
        permissions: list[str] | None = None,
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("name required")
        proto = protocol.lower().strip()
        if proto not in PROTOCOLS:
            raise ValidationError(f"protocol must be one of {list(PROTOCOLS)}")
        ad = adapter.lower().strip()
        if ad not in ADAPTERS:
            raise ValidationError(f"adapter must be one of {list(ADAPTERS)}")
        iid = _id("eip_reg")
        return self.store.eip_registry.save(
            iid,
            {
                "integration_id": iid,
                "name": name,
                "version": version,
                "protocol": proto,
                "adapter": ad,
                "status": "registered",
                "owner": owner,
                "connection": connection or {},
                "permissions": permissions or ["read"],
                "change_log": [{"action": "register", "at": _now()}],
                "at": _now(),
            },
        )

    def get(self, *, integration_id: str) -> dict[str, Any]:
        item = self.store.eip_registry.get(integration_id)
        if item is None:
            raise NotFoundError(f"integration not found: {integration_id}")
        return item

    def update_status(self, *, integration_id: str, status: str) -> dict[str, Any]:
        item = self.get(integration_id=integration_id)
        st = status.lower().strip()
        if st not in INTEGRATION_STATUSES:
            raise ValidationError(f"status must be one of {list(INTEGRATION_STATUSES)}")
        item["status"] = st
        item["change_log"] = list(item.get("change_log") or []) + [{"action": st, "at": _now()}]
        item["at"] = _now()
        return self.store.eip_registry.save(integration_id, item)

    def status(self) -> dict[str, Any]:
        return {
            "integrations": self.store.eip_registry.count(),
            "protocols": list(PROTOCOLS),
            "adapters": list(ADAPTERS),
        }
