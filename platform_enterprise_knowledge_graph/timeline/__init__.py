"""Knowledge Timeline — Sprint 24.2."""

from __future__ import annotations

from typing import Any


class KnowledgeTimeline:
    def __init__(self) -> None:
        self._events: dict[str, list[dict[str, Any]]] = {}

    def append(self, *, entity_id: str, event_type: str, summary: str, meta: dict[str, Any] | None = None) -> dict[str, Any]:
        if not entity_id or not event_type:
            raise ValueError("entity_id and event_type are required")
        item = {
            "entity_id": entity_id,
            "event_type": event_type,
            "summary": summary,
            "meta": dict(meta or {}),
        }
        self._events.setdefault(entity_id, []).append(item)
        return dict(item)

    def for_entity(self, entity_id: str) -> dict[str, Any]:
        events = list(self._events.get(entity_id) or [])
        return {
            "entity_id": entity_id,
            "events": events,
            "created": [e for e in events if e["event_type"] == "created"],
            "changes": [e for e in events if e["event_type"] == "change"],
            "processes": [e for e in events if e["event_type"] == "process"],
            "documents": [e for e in events if e["event_type"] == "document"],
            "ai_recommendations": [e for e in events if e["event_type"] == "ai_recommendation"],
            "owner_approvals": [e for e in events if e["event_type"] == "owner_approval"],
        }
