"""Platform internal event package."""

from events.base_event import BaseEvent
from events.event_bus import PlatformEventBus, publish, reset_subscribers, subscribe
from events.request_events import (
    ManagerReassignedEvent,
    RequestAssignedEvent,
    RequestCompletedEvent,
    RequestCreatedEvent,
    RequestOverdueEvent,
)

# Legacy platform EventBus (SQLite/platform_events table) — backward compatible imports.
from platform_events_legacy import (  # noqa: E402
    EventBus,
    PlatformEvent,
    reset_event_bus_for_tests,
)

__all__ = [
    "BaseEvent",
    "PlatformEventBus",
    "publish",
    "subscribe",
    "reset_subscribers",
    "RequestCreatedEvent",
    "RequestAssignedEvent",
    "RequestCompletedEvent",
    "RequestOverdueEvent",
    "ManagerReassignedEvent",
    "EventBus",
    "PlatformEvent",
    "reset_event_bus_for_tests",
]
