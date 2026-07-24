"""Enterprise Knowledge Graph core — Sprint 24.2."""

from __future__ import annotations

from typing import Any

from platform_enterprise_knowledge_graph.models import ENTITY_TYPES


class KnowledgeGraph:
    def __init__(self) -> None:
        self._entities: dict[str, dict[str, Any]] = {}

    def upsert(
        self,
        *,
        entity_id: str,
        entity_type: str,
        properties: dict[str, Any] | None = None,
        labels: list[str] | None = None,
    ) -> dict[str, Any]:
        if not entity_id:
            raise ValueError("entity_id is required")
        entity_type = (entity_type or "").lower()
        if entity_type not in ENTITY_TYPES:
            raise ValueError(f"unsupported entity type: {entity_type}")
        existing = self._entities.get(entity_id, {})
        entity = {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "properties": {**(existing.get("properties") or {}), **(properties or {})},
            "labels": list(labels or existing.get("labels") or []),
            "ai_allowed": existing.get("ai_allowed", True),
            "archived": existing.get("archived", False),
            "confirmed": existing.get("confirmed", False),
            "strength": float(existing.get("strength", 1.0)),
        }
        self._entities[entity_id] = entity
        return dict(entity)

    def get(self, entity_id: str) -> dict[str, Any] | None:
        e = self._entities.get(entity_id)
        return dict(e) if e else None

    def list_entities(self, *, entity_type: str | None = None, include_archived: bool = False) -> list[dict[str, Any]]:
        items = [dict(e) for e in self._entities.values()]
        if entity_type:
            items = [e for e in items if e.get("entity_type") == entity_type.lower()]
        if not include_archived:
            items = [e for e in items if not e.get("archived")]
        return items

    def set_flags(self, entity_id: str, *, ai_allowed: bool | None = None, archived: bool | None = None, confirmed: bool | None = None, strength: float | None = None) -> dict[str, Any]:
        e = self._entities.get(entity_id)
        if not e:
            raise ValueError(f"unknown entity: {entity_id}")
        if ai_allowed is not None:
            e["ai_allowed"] = bool(ai_allowed)
        if archived is not None:
            e["archived"] = bool(archived)
        if confirmed is not None:
            e["confirmed"] = bool(confirmed)
        if strength is not None:
            e["strength"] = float(strength)
        return dict(e)
