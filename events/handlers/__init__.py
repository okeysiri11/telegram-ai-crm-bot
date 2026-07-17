# Register default platform internal event handlers.

from __future__ import annotations

import logging

from audit.audit_service import audit_service
from events.event_bus import subscribe
from events.handlers.metrics_handler import MetricsEventHandler
from events.handlers.notification_handler import NotificationEventHandler
from events.handlers.sla_handler import SLAEventHandler
from events.request_events import (
    ManagerReassignedEvent,
    RequestAssignedEvent,
    RequestCompletedEvent,
    RequestCreatedEvent,
    RequestOverdueEvent,
)

logger = logging.getLogger(__name__)

_registered = False


def register_platform_event_handlers() -> None:
    global _registered
    if _registered:
        return

    handlers = (
        (RequestCreatedEvent, NotificationEventHandler.handle, "notification"),
        (RequestCreatedEvent, MetricsEventHandler.handle, "metrics"),
        (RequestCreatedEvent, SLAEventHandler.handle, "sla"),
        (RequestAssignedEvent, MetricsEventHandler.handle, "metrics_assigned"),
        (RequestAssignedEvent, SLAEventHandler.handle, "sla_assigned"),
        (RequestCompletedEvent, MetricsEventHandler.handle, "metrics_completed"),
        (RequestCompletedEvent, SLAEventHandler.handle, "sla_completed"),
        (ManagerReassignedEvent, MetricsEventHandler.handle, "metrics_reassigned"),
        (RequestOverdueEvent, SLAEventHandler.handle, "sla_overdue"),
        (RequestOverdueEvent, NotificationEventHandler.handle, "notification_overdue"),
    )

    for event_type, handler, handler_id in handlers:
        subscribe(event_type, handler, handler_id=handler_id)

    audit_service.subscribe_to_event_bus()

    _registered = True
    logger.info(
        "platform_internal_event_handlers_registered",
        extra={"handler_count": len(handlers) + 5},
    )


def reset_handler_registration() -> None:
    global _registered
    _registered = False
    audit_service.reset_subscription()
