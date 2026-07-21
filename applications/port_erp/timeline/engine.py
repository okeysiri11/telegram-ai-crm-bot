# Timeline Engine — asset event history.

from __future__ import annotations

from applications.port_erp.shared.store import PortStore, port_store
from applications.port_erp.tracking.models import TimelineEvent


class TimelineEngine:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def record(self, event: TimelineEvent) -> TimelineEvent:
        return self._store.timeline_events.save(event.event_id, event)

    def for_asset(self, asset_type: str, asset_id: str) -> list[TimelineEvent]:
        items = [
            e
            for e in self._store.timeline_events.list_all()
            if e.asset_type == asset_type and e.asset_id == asset_id
        ]
        return sorted(items, key=lambda e: e.occurred_at)

    def recent(self, *, limit: int = 50) -> list[TimelineEvent]:
        items = sorted(self._store.timeline_events.list_all(), key=lambda e: e.occurred_at, reverse=True)
        return items[:limit]


timeline_engine = TimelineEngine()
