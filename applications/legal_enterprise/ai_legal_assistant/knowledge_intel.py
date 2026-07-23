"""Knowledge intelligence — graph navigation, concepts, entities."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.legal_enterprise.config import DEFAULT_CONFIG
from applications.legal_enterprise.shared.exceptions import ValidationError
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class KnowledgeIntelligence:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.bases = list(DEFAULT_CONFIG.aa_knowledge_bases)

    def navigate(self, *, from_node: str, relation: str = "related_to") -> dict[str, Any]:
        if not from_node:
            raise ValidationError("from_node required")
        nid = _id("aa_nav")
        return self.store.aa_graph_nav.save(
            nid,
            {
                "nav_id": nid,
                "from_node": from_node,
                "relation": relation,
                "neighbors": [f"{from_node}->authority", f"{from_node}->concept"],
                "at": _now(),
            },
        )

    def map_concept(self, *, concept: str, related: list[str] | None = None) -> dict[str, Any]:
        if not concept:
            raise ValidationError("concept required")
        cid = _id("aa_concept")
        return self.store.aa_concepts.save(
            cid,
            {
                "concept_id": cid,
                "concept": concept,
                "related": related or ["obligation", "liability", "remedy"],
                "at": _now(),
            },
        )

    def discover_relationship(
        self, *, from_entity: str, to_entity: str, relation: str = "cites"
    ) -> dict[str, Any]:
        if not from_entity or not to_entity:
            raise ValidationError("from_entity and to_entity required")
        rid = _id("aa_rel")
        return self.store.aa_relationships.save(
            rid,
            {
                "relationship_id": rid,
                "from_entity": from_entity,
                "to_entity": to_entity,
                "relation": relation,
                "at": _now(),
            },
        )

    def terminology(self, *, term: str, definition: str = "") -> dict[str, Any]:
        if not term:
            raise ValidationError("term required")
        tid = _id("aa_term")
        return self.store.aa_terminology.save(
            tid,
            {
                "term_id": tid,
                "term": term,
                "definition": definition or f"Legal definition of {term}",
                "at": _now(),
            },
        )

    def resolve_entity(self, *, name: str, entity_type: str = "authority") -> dict[str, Any]:
        if not name:
            raise ValidationError("name required")
        eid = _id("aa_ent")
        return self.store.aa_entities.save(
            eid,
            {
                "entity_id": eid,
                "name": name,
                "entity_type": entity_type,
                "canonical": name.strip().title(),
                "at": _now(),
            },
        )

    def publish(self, *, base: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if base not in self.bases:
            raise ValidationError(f"base must be one of {self.bases}")
        if not key:
            raise ValidationError("key required")
        rid = _id("aa_kg")
        return self.store.aa_knowledge.save(
            rid,
            {
                "entry_id": rid,
                "base": base,
                "key": key,
                "payload": payload or {},
                "graph_node": f"aa:{base}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "entries": self.store.aa_knowledge.count(),
            "nav": self.store.aa_graph_nav.count(),
            "concepts": self.store.aa_concepts.count(),
            "relationships": self.store.aa_relationships.count(),
            "terminology": self.store.aa_terminology.count(),
            "entities": self.store.aa_entities.count(),
            "bases": self.bases,
        }
