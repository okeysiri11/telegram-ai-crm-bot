"""Unified knowledge graph — entities, relationships, ontology, linking, versioning."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class UnifiedKnowledgeGraph:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.entity_types = list(DEFAULT_CONFIG.kg_entity_types)

    def register_entity(
        self,
        *,
        name: str,
        entity_type: str,
        platform: str = "",
        attributes: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        et = entity_type.lower().strip()
        if et not in self.entity_types:
            raise ValidationError(f"entity_type must be one of {self.entity_types}")
        if not name:
            raise ValidationError("name required")
        eid = _id("kg_ent")
        return self.store.kg_entities.save(
            eid,
            {
                "entity_id": eid,
                "name": name,
                "entity_type": et,
                "platform": platform.lower(),
                "attributes": attributes or {},
                "version": 1,
                "at": _now(),
            },
        )

    def relate(
        self,
        *,
        from_entity_id: str,
        to_entity_id: str,
        relation: str,
        weight: float = 1.0,
    ) -> dict[str, Any]:
        if not from_entity_id or not to_entity_id or not relation:
            raise ValidationError("from_entity_id, to_entity_id, and relation required")
        if self.store.kg_entities.get(from_entity_id) is None:
            raise NotFoundError(f"entity not found: {from_entity_id}")
        if self.store.kg_entities.get(to_entity_id) is None:
            raise NotFoundError(f"entity not found: {to_entity_id}")
        rid = _id("kg_rel")
        return self.store.kg_relationships.save(
            rid,
            {
                "relationship_id": rid,
                "from_entity_id": from_entity_id,
                "to_entity_id": to_entity_id,
                "relation": relation,
                "weight": float(weight),
                "at": _now(),
            },
        )

    def build_graph(self, *, label: str = "enterprise") -> dict[str, Any]:
        gid = _id("kg_graph")
        return self.store.kg_graphs.save(
            gid,
            {
                "graph_id": gid,
                "label": label,
                "entities": self.store.kg_entities.count(),
                "relationships": self.store.kg_relationships.count(),
                "at": _now(),
            },
        )

    def link_cross_platform(
        self, *, entity_id: str, platform: str, external_id: str
    ) -> dict[str, Any]:
        if self.store.kg_entities.get(entity_id) is None:
            raise NotFoundError(f"entity not found: {entity_id}")
        if not platform or not external_id:
            raise ValidationError("platform and external_id required")
        lid = _id("kg_link")
        return self.store.kg_links.save(
            lid,
            {
                "link_id": lid,
                "entity_id": entity_id,
                "platform": platform.lower(),
                "external_id": external_id,
                "at": _now(),
            },
        )

    def register_ontology(
        self, *, name: str, concepts: list[str] | None = None, version: str = "1.0"
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("name required")
        oid = _id("kg_ont")
        return self.store.kg_ontologies.save(
            oid,
            {
                "ontology_id": oid,
                "name": name,
                "concepts": concepts or [],
                "version": version,
                "at": _now(),
            },
        )

    def version_graph(self, *, graph_id: str, note: str = "") -> dict[str, Any]:
        graph = self.store.kg_graphs.get(graph_id)
        if graph is None:
            raise NotFoundError(f"graph not found: {graph_id}")
        vid = _id("kg_ver")
        return self.store.kg_versions.save(
            vid,
            {
                "version_id": vid,
                "graph_id": graph_id,
                "entities": graph["entities"],
                "relationships": graph["relationships"],
                "note": note,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "entities": self.store.kg_entities.count(),
            "relationships": self.store.kg_relationships.count(),
            "graphs": self.store.kg_graphs.count(),
            "links": self.store.kg_links.count(),
            "ontologies": self.store.kg_ontologies.count(),
            "versions": self.store.kg_versions.count(),
            "entity_types": self.entity_types,
        }
