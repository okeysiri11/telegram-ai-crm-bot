"""Ontology — entity/relation types for knowledge graph."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.knowledge_platform.models import ENTITY_KINDS
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


DEFAULT_RELATIONS = (
    "owns",
    "works_on",
    "references",
    "related_to",
    "managed_by",
    "produced_by",
)


class Ontology:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def define(self, *, name: str, entity_kinds: list[str] | None = None, relations: list[str] | None = None) -> dict[str, Any]:
        if not name:
            raise ValidationError("name is required")
        kinds = entity_kinds or list(ENTITY_KINDS)
        for k in kinds:
            if k not in ENTITY_KINDS:
                raise ValidationError(f"unknown entity kind: {k}")
        oid = _id("ekp_ont")
        return self.store.ekp_ontologies.save(
            oid,
            {
                "ontology_id": oid,
                "name": name.strip(),
                "entity_kinds": kinds,
                "relations": relations or list(DEFAULT_RELATIONS),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"ontologies": self.store.ekp_ontologies.count(), "entity_kinds": list(ENTITY_KINDS)}
