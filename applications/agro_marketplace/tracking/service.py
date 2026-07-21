# Shipment tracking events and timeline.

from __future__ import annotations

from applications.agro_marketplace.export.models import TrackingEvent
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class TrackingService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def record(self, event: TrackingEvent) -> TrackingEvent:
        return self._store.tracking_events.save(event.event_id, event)

    def timeline(self, shipment_id: str) -> list[TrackingEvent]:
        items = [e for e in self._store.tracking_events.list_all() if e.shipment_id == shipment_id]
        return sorted(items, key=lambda e: e.occurred_at)

    def latest(self, shipment_id: str) -> TrackingEvent | None:
        items = self.timeline(shipment_id)
        return items[-1] if items else None


tracking_service = TrackingService()
