"""contact master entity."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.data_platform.entities import upsert_entity
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class ContactEntity:
    entity_type = "contact"

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def create(self, *, name: str, attributes: dict[str, Any] | None = None, owner: str = "system") -> dict[str, Any]:
        return upsert_entity(
            self.store,
            entity_type=self.entity_type,
            name=name,
            attributes=attributes,
            owner=owner,
        )
