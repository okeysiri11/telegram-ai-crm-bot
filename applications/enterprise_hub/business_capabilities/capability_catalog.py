
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

from applications.enterprise_hub.business_capabilities.capabilities import (
    DEFAULT_DEPENDENCIES,
    all_definitions,
)
from applications.enterprise_hub.business_capabilities.capability_registry import CapabilityRegistry


class CapabilityCatalog:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.registry = CapabilityRegistry(self.store)

    def seed(self) -> dict[str, Any]:
        created = []
        for definition in all_definitions():
            if self.registry.find_by_key(definition["key"]):
                continue
            created.append(self.registry.register(**definition))
        catalog_id = _id("ebc_cat")
        record = {
            "catalog_id": catalog_id,
            "seeded": len(created),
            "total": len(self.registry.list_all()),
            "dependency_pairs": list(DEFAULT_DEPENDENCIES),
            "seeded_at": _now(),
        }
        self.store.ebc_catalogs.save(catalog_id, record)
        return record

    def list_catalog(self) -> list[dict[str, Any]]:
        return self.registry.list_all()

    def status(self) -> dict[str, Any]:
        return {"catalogs": len(self.store.ebc_catalogs.list_all()), "capabilities": len(self.registry.list_all())}
