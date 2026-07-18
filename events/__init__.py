"""Platform internal event package."""

from events.adapters.legacy_adapter import (
    publish_legacy_to_platform_bus,
    register_legacy_handlers_on_platform_bus,
    reset_legacy_bridge_registration,
)
from events.adapters.crm_adapter import publish_crm_to_platform_bus
from events.base_event import BaseEvent
from events.event_bus import PlatformEventBus, publish, reset_subscribers, subscribe
from events.generic_events import GenericPlatformEvent
from events.publisher import (
    publish as publish_domain,
    publish_ai,
    publish_plugin,
    publish_skill,
    publish_sla,
    publish_workflow,
)
from events.request_events import (
    ManagerEscalationEvent,
    ManagerReassignedEvent,
    RequestAssignedEvent,
    RequestCompletedEvent,
    RequestCreatedEvent,
    RequestOverdueEvent,
)

# Legacy platform EventBus (SQLite/platform_events table) — via platform_legacy adapter.
from platform_legacy import legacy  # noqa: E402

PlatformEvent = legacy.events.legacy_platform_event_class()
EventBus = legacy.events.legacy_event_bus_class()


def reset_event_bus_for_tests() -> None:
    legacy.events.reset_event_bus_for_tests()

__all__ = [
    "BaseEvent",
    "GenericPlatformEvent",
    "PlatformEventBus",
    "publish",
    "publish_domain",
    "publish_ai",
    "publish_skill",
    "publish_workflow",
    "publish_plugin",
    "publish_sla",
    "publish_legacy_to_platform_bus",
    "publish_crm_to_platform_bus",
    "register_legacy_handlers_on_platform_bus",
    "reset_legacy_bridge_registration",
    "subscribe",
    "reset_subscribers",
    "RequestCreatedEvent",
    "RequestAssignedEvent",
    "RequestCompletedEvent",
    "RequestOverdueEvent",
    "ManagerEscalationEvent",
    "ManagerReassignedEvent",
    "EventBus",
    "PlatformEvent",
    "reset_event_bus_for_tests",
]
