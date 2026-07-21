# Event store — durable log of published bus events.

from __future__ import annotations

from typing import Any

from ecosystem.communication.models import BusEvent, EventCategory
from ecosystem.shared.exceptions import NotFoundError
from ecosystem.shared.store import EcosystemStore, ecosystem_store


class EventStore:
    """Append-only event store for the global event bus."""

    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store

    def append(self, event: BusEvent) -> BusEvent:
        self._store.event_store_log.save(event.event_id, event)
        return event

    def get(self, event_id: str) -> BusEvent:
        event = self._store.event_store_log.get(event_id)
        if event is None:
            raise NotFoundError("StoredEvent", event_id)
        return event

    def replay(
        self,
        *,
        category: EventCategory | None = None,
        source_application: str = "",
        since: float = 0.0,
        limit: int = 500,
    ) -> list[BusEvent]:
        events = self._store.event_store_log.list_all()
        if category:
            events = [e for e in events if e.category == category]
        if source_application:
            events = [e for e in events if e.source_application == source_application]
        if since:
            events = [e for e in events if e.created_at >= since]
        return sorted(events, key=lambda e: e.created_at)[:limit]

    def stats(self) -> dict[str, Any]:
        events = self._store.event_store_log.list_all()
        by_category: dict[str, int] = {}
        for event in events:
            by_category[event.category.value] = by_category.get(event.category.value, 0) + 1
        return {"total": len(events), "by_category": by_category}


event_store = EventStore()
