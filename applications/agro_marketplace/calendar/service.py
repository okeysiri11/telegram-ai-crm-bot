# Calendar events for farmers, buyers and logistics scheduling.

from __future__ import annotations

from applications.agro_marketplace.portal.models import CalendarEvent
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class CalendarService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def create(self, event: CalendarEvent) -> CalendarEvent:
        if not event.title or not event.user_id:
            raise ValidationError("title and user_id are required")
        return self._store.calendar_events.save(event.event_id, event)

    def get(self, event_id: str) -> CalendarEvent:
        event = self._store.calendar_events.get(event_id)
        if event is None:
            raise NotFoundError("CalendarEvent", event_id)
        return event

    def list_for(self, user_id: str) -> list[CalendarEvent]:
        items = [e for e in self._store.calendar_events.list_all() if e.user_id == user_id]
        return sorted(items, key=lambda e: e.starts_at)


calendar_service = CalendarService()
