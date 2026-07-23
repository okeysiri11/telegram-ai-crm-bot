"""Metadata manager — schemas, attributes, constraints, indexes, dependencies."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class MetadataManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def register_schema(
        self,
        *,
        name: str,
        entity_type: str,
        attributes: list[dict[str, Any]] | None = None,
        constraints: list[str] | None = None,
        indexes: list[str] | None = None,
        dependencies: list[str] | None = None,
    ) -> dict[str, Any]:
        if not name or not entity_type:
            raise ValidationError("name and entity_type required")
        sid = _id("edp_meta")
        return self.store.edp_metadata.save(
            sid,
            {
                "schema_id": sid,
                "name": name,
                "entity_type": entity_type.lower(),
                "attributes": attributes or [],
                "constraints": constraints or [],
                "indexes": indexes or [],
                "dependencies": dependencies or [],
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"schemas": self.store.edp_metadata.count()}
