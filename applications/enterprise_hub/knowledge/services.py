"""Unified knowledge dashboards and meta knowledge graph."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class UnifiedKnowledgeMeta:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.bases = list(DEFAULT_CONFIG.kg_knowledge_bases)

    def publish(self, *, base: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if base not in self.bases:
            raise ValidationError(f"base must be one of {self.bases}")
        if not key:
            raise ValidationError("key required")
        eid = _id("kg_kg")
        return self.store.kg_knowledge.save(
            eid,
            {
                "entry_id": eid,
                "base": base,
                "key": key,
                "payload": payload or {},
                "graph_node": f"ukg:{base}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.kg_knowledge.count(), "bases": self.bases}


class UnifiedKnowledgeDashboard:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.types = list(DEFAULT_CONFIG.kg_dashboard_types)

    def render(self, *, dashboard_type: str = "knowledge") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "knowledge": {
                "entities": self.store.kg_entities.count(),
                "graphs": self.store.kg_graphs.count(),
                "ontologies": self.store.kg_ontologies.count(),
            },
            "entity": {
                "entities": self.store.kg_entities.count(),
                "links": self.store.kg_links.count(),
            },
            "relationship": {
                "relationships": self.store.kg_relationships.count(),
            },
            "ai_memory": {
                "memories": self.store.kg_memories.count(),
            },
            "semantic": {
                "semantics": self.store.kg_semantics.count(),
                "insights": self.store.kg_ai_insights.count(),
                "contexts": self.store.kg_contexts.count(),
            },
        }[dashboard_type]
        did = _id("kg_dash")
        return self.store.kg_dashboards.save(
            did,
            {
                "dashboard_id": did,
                "dashboard_type": dashboard_type,
                "metrics": metrics,
                "generated_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.kg_dashboards.count(), "types": self.types}
