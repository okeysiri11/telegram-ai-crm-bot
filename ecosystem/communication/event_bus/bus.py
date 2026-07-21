# Global event bus — domain, application, system, AI, workflow events.

from __future__ import annotations

from typing import Any, Callable, Awaitable

from events.publisher import publish

from ecosystem.communication.events import EventConsumedEvent, EventPublishedEvent
from ecosystem.communication.models import BusEvent, EventCategory, Subscription
from ecosystem.shared.store import EcosystemStore, ecosystem_store


class EventBus:
    """Global event bus for cross-application domain and system events."""

    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store
        self._handlers: dict[str, list[Callable[..., Awaitable[None]]]] = {}

    async def publish(
        self,
        event_name: str,
        payload: dict[str, Any],
        *,
        category: EventCategory = EventCategory.APPLICATION,
        source_application: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> BusEvent:
        event = BusEvent(
            category=category,
            event_name=event_name,
            source_application=source_application,
            payload=payload,
            metadata=metadata or {},
        )
        self._store.bus_events.save(event.event_id, event)
        self._store.event_store_log.save(event.event_id, event)
        await publish(
            EventPublishedEvent(
                bus_event_id=event.event_id,
                event_name=event_name,
                category=category.value,
                source_application=source_application,
            )
        )
        await self._dispatch_to_subscribers(event)
        return event

    async def publish_domain(self, event_name: str, payload: dict[str, Any], *, source: str = "") -> BusEvent:
        return await self.publish(event_name, payload, category=EventCategory.DOMAIN, source_application=source)

    async def publish_application(self, event_name: str, payload: dict[str, Any], *, source: str = "") -> BusEvent:
        return await self.publish(event_name, payload, category=EventCategory.APPLICATION, source_application=source)

    async def publish_system(self, event_name: str, payload: dict[str, Any], *, source: str = "") -> BusEvent:
        return await self.publish(event_name, payload, category=EventCategory.SYSTEM, source_application=source)

    async def publish_ai(self, event_name: str, payload: dict[str, Any], *, source: str = "") -> BusEvent:
        return await self.publish(event_name, payload, category=EventCategory.AI, source_application=source)

    async def publish_workflow(self, event_name: str, payload: dict[str, Any], *, source: str = "") -> BusEvent:
        return await self.publish(event_name, payload, category=EventCategory.WORKFLOW, source_application=source)

    def subscribe_handler(self, topic: str, handler: Callable[..., Awaitable[None]]) -> None:
        self._handlers.setdefault(topic, []).append(handler)

    def list_events(
        self,
        *,
        category: EventCategory | None = None,
        source_application: str = "",
        limit: int = 100,
    ) -> list[BusEvent]:
        events = self._store.bus_events.list_all()
        if category:
            events = [e for e in events if e.category == category]
        if source_application:
            events = [e for e in events if e.source_application == source_application]
        return sorted(events, key=lambda e: e.created_at, reverse=True)[:limit]

    def get_event(self, event_id: str) -> BusEvent | None:
        return self._store.bus_events.get(event_id)

    async def _dispatch_to_subscribers(self, event: BusEvent) -> None:
        subscribers = [
            s
            for s in self._store.subscriptions.list_all()
            if s.is_active and self._matches(s, event)
        ]
        for sub in subscribers:
            await publish(
                EventConsumedEvent(
                    bus_event_id=event.event_id,
                    consumer_application=sub.application_id,
                    topic=sub.topic,
                )
            )
        for topic, handlers in self._handlers.items():
            if topic == "*" or topic == event.event_name or topic == event.category.value:
                for handler in handlers:
                    await handler(event)

    @staticmethod
    def _matches(subscription: Subscription, event: BusEvent) -> bool:
        if subscription.topic in ("*", event.event_name, event.category.value):
            if not subscription.event_filter:
                return True
            return subscription.event_filter in event.event_name or subscription.event_filter == event.category.value
        return False


event_bus = EventBus()
