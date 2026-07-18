# Register default platform internal event handlers.

from __future__ import annotations

import logging

from audit.audit_service import audit_service
from events.event_bus import subscribe
from events.handlers.owner_notification_handler import OwnerNotificationHandler
from events.handlers.metrics_handler import MetricsEventHandler
from events.handlers.notification_handler import NotificationEventHandler
from events.handlers.sla_handler import SLAEventHandler
from events.owner_events import OwnerEscalationEvent
from events.request_events import (
    ManagerEscalationEvent,
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
        (ManagerEscalationEvent, NotificationEventHandler.handle, "notification_escalation"),
        (OwnerEscalationEvent, OwnerNotificationHandler.handle, "owner_notification"),
        (OwnerEscalationEvent, MetricsEventHandler.handle, "metrics_owner_escalation"),
    )

    for event_type, handler, handler_id in handlers:
        subscribe(event_type, handler, handler_id=handler_id)

    audit_service.subscribe_to_event_bus()

    from services.kpi_service import kpi_service

    kpi_service.subscribe_to_event_bus()

    from services.sla_timer_service import sla_timer_service

    sla_timer_service.subscribe_to_event_bus()

    from services.manager_pool_service import manager_pool_service

    manager_pool_service.subscribe_to_event_bus()

    from services.smart_assignment_service import smart_assignment_service

    smart_assignment_service.subscribe_to_event_bus()

    from events.configuration_events import ConfigurationChangedEvent
    from events.handlers.configuration_handler import ConfigurationEventHandler

    subscribe(
        ConfigurationChangedEvent,
        ConfigurationEventHandler.handle,
        handler_id="configuration_hot_reload",
    )

    from workflow.workflow_kpi import workflow_kpi_service

    workflow_kpi_service.subscribe_to_event_bus()

    from platform_realtime.event_dispatcher import register_realtime_event_handlers

    register_realtime_event_handlers()

    from events.adapters.legacy_adapter import register_legacy_handlers_on_platform_bus

    register_legacy_handlers_on_platform_bus()

    _registered = True
    logger.info(
        "platform_internal_event_handlers_registered",
        extra={"handler_count": len(handlers) + 14},
    )


def reset_handler_registration() -> None:
    global _registered
    _registered = False
    audit_service.reset_subscription()
    from services.kpi_service import kpi_service
    from services.sla_timer_service import sla_timer_service

    kpi_service.reset_subscription()
    sla_timer_service.reset_subscription()
    from workflow.workflow_kpi import workflow_kpi_service

    workflow_kpi_service.reset_subscription()
    from platform_realtime.event_dispatcher import reset_realtime_event_handlers

    reset_realtime_event_handlers()
    from events.adapters.legacy_adapter import reset_legacy_bridge_registration

    reset_legacy_bridge_registration()
