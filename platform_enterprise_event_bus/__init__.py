"""Enterprise Event Bus — Sprint 36.1 public exports.

SoR remains events.event_bus.PlatformEventBus.
This package is the enterprise control plane (topics, DLQ, replay, API, UI).
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "EnterpriseEventBus",
    "EnterpriseEventBusService",
    "enterprise_event_bus",
    "enterprise_event_bus_service",
    "EnterpriseEvent",
    "EventPriority",
    "EventPublisher",
    "EventSubscriber",
    "EventDispatcher",
    "EventRouter",
    "EventBroker",
    "EventStore",
    "EventReplayEngine",
    "EventFilter",
    "EventValidator",
    "EventSerializer",
    "EventDeserializer",
    "DeadLetterQueue",
    "RetryManager",
    "TopicManager",
]


def __getattr__(name: str) -> Any:
    if name in {"EnterpriseEventBus", "enterprise_event_bus"}:
        from platform_enterprise_event_bus.bus import EnterpriseEventBus, enterprise_event_bus

        return EnterpriseEventBus if name == "EnterpriseEventBus" else enterprise_event_bus
    if name in {"EnterpriseEventBusService", "enterprise_event_bus_service"}:
        from platform_enterprise_event_bus.service import (
            EnterpriseEventBusService,
            enterprise_event_bus_service,
        )

        return EnterpriseEventBusService if name == "EnterpriseEventBusService" else enterprise_event_bus_service
    if name in {"EnterpriseEvent", "EventPriority"}:
        from platform_enterprise_event_bus import models as _m

        return getattr(_m, name)
    if name in {
        "EventPublisher",
        "EventSubscriber",
        "EventDispatcher",
        "EventRouter",
        "EventBroker",
        "EventReplayEngine",
    }:
        from platform_enterprise_event_bus import bus as _b

        return getattr(_b, name)
    if name in {
        "EventStore",
        "DeadLetterQueue",
        "RetryManager",
        "TopicManager",
    }:
        from platform_enterprise_event_bus import components as _c

        return getattr(_c, name)
    if name in {"EventFilter", "EventValidator", "EventSerializer", "EventDeserializer"}:
        from platform_enterprise_event_bus import filters as _f

        return getattr(_f, name)
    raise AttributeError(f"module 'platform_enterprise_event_bus' has no attribute {name!r}")
