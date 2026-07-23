"""Knowledge graph — entities and relationships."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.knowledge_platform.models import ENTITY_KINDS
from applications.enterprise_hub.knowledge_platform.ontology import DEFAULT_RELATIONS
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class KnowledgeGraph:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def add_entity(self, *, kind: str, name: str, meta: dict[str, Any] | None = None) -> dict[str, Any]:
        k = kind.lower().strip()
        if k not in ENTITY_KINDS:
            raise ValidationError(f"kind must be one of {list(ENTITY_KINDS)}")
        if not name:
            raise ValidationError("name is required")
        eid = _id("ekp_ent")
        return self.store.ekp_entities.save(
            eid,
            {
                "entity_id": eid,
                "kind": k,
                "name": name.strip(),
                "meta": meta or {},
                "at": _now(),
            },
        )

    def link(
        self,
        *,
        source_id: str,
        target_id: str,
        relation: str = "related_to",
    ) -> dict[str, Any]:
        if not self.store.ekp_entities.get(source_id):
            raise NotFoundError(f"source not found: {source_id}")
        if not self.store.ekp_entities.get(target_id):
            raise NotFoundError(f"target not found: {target_id}")
        rel = relation.lower().strip()
        if rel not in DEFAULT_RELATIONS:
            raise ValidationError(f"relation must be one of {list(DEFAULT_RELATIONS)}")
        rid = _id("ekp_rel")
        return self.store.ekp_relations.save(
            rid,
            {
                "relation_id": rid,
                "source_id": source_id,
                "target_id": target_id,
                "relation": rel,
                "at": _now(),
            },
        )

    def neighbors(self, *, entity_id: str) -> dict[str, Any]:
        if not self.store.ekp_entities.get(entity_id):
            raise NotFoundError(f"entity not found: {entity_id}")
        links = [
            r
            for r in self.store.ekp_relations.list_all()
            if r.get("source_id") == entity_id or r.get("target_id") == entity_id
        ]
        return {"entity_id": entity_id, "links": links, "count": len(links)}

    def status(self) -> dict[str, Any]:
        return {
            "entities": self.store.ekp_entities.count(),
            "relations": self.store.ekp_relations.count(),
        }
