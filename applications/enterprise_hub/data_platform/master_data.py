"""Master Data Management — unified reference data."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.data_platform.entities import upsert_entity
from applications.enterprise_hub.data_platform.models import ENTITY_TYPES, MASTER_DOMAINS
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class MasterData:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.domains = list(MASTER_DOMAINS)

    def upsert(
        self,
        *,
        entity_type: str,
        name: str,
        attributes: dict[str, Any] | None = None,
        source: str = "mdm",
        owner: str = "system",
    ) -> dict[str, Any]:
        return upsert_entity(
            self.store,
            entity_type=entity_type,
            name=name,
            attributes=attributes,
            source=source,
            owner=owner,
        )

    def get(self, *, entity_id: str) -> dict[str, Any]:
        item = self.store.edp_entities.get(entity_id)
        if item is None:
            raise NotFoundError(f"entity not found: {entity_id}")
        return item

    def relate(
        self,
        *,
        from_entity_id: str,
        to_entity_id: str,
        relation: str,
    ) -> dict[str, Any]:
        if self.store.edp_entities.get(from_entity_id) is None:
            raise NotFoundError(f"entity not found: {from_entity_id}")
        if self.store.edp_entities.get(to_entity_id) is None:
            raise NotFoundError(f"entity not found: {to_entity_id}")
        if not relation:
            raise ValidationError("relation required")
        import uuid
        from datetime import datetime, timezone

        rid = f"edp_rel_{uuid.uuid4().hex[:12]}"
        return self.store.edp_relationships.save(
            rid,
            {
                "relationship_id": rid,
                "from_entity_id": from_entity_id,
                "to_entity_id": to_entity_id,
                "relation": relation,
                "at": datetime.now(timezone.utc).isoformat(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "entities": self.store.edp_entities.count(),
            "relationships": self.store.edp_relationships.count(),
            "entity_types": list(ENTITY_TYPES),
            "domains": self.domains,
        }
