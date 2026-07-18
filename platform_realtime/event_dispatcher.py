# EventBus → Realtime dispatcher — maps domain events to channels and widgets.

from __future__ import annotations

import asyncio
import logging
from typing import Any

from events.base_event import BaseEvent
from events.configuration_events import ConfigurationChangedEvent
from events.manager_pool_events import (
    ManagerAssignedEvent,
    ManagerReleasedEvent,
    ManagerUnavailableEvent,
)
from events.request_events import (
    ManagerEscalationEvent,
    ManagerReassignedEvent,
    RequestAssignedEvent,
    RequestCompletedEvent,
    RequestCreatedEvent,
    RequestOverdueEvent,
)
from events.smart_assignment_events import SmartAssignmentCompletedEvent
from events.workflow_events import (
    WorkflowCancelledEvent,
    WorkflowCompletedEvent,
    WorkflowStartedEvent,
    WorkflowStepCompletedEvent,
)
from platform_realtime.models import RealtimeChannel, RealtimeMessage
from platform_realtime.realtime_hub import realtime_hub

logger = logging.getLogger(__name__)

_registered = False

# Event type → (channels, affected dashboard widgets)
_EVENT_ROUTING: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "RequestCreatedEvent": (
        (RealtimeChannel.REQUESTS.value, RealtimeChannel.DASHBOARD.value, RealtimeChannel.SYSTEM.value),
        ("active_requests", "requests_by_vertical", "recent_events"),
    ),
    "RequestAssignedEvent": (
        (RealtimeChannel.REQUESTS.value, RealtimeChannel.MANAGERS.value, RealtimeChannel.DASHBOARD.value),
        ("manager_load", "active_requests", "recent_events"),
    ),
    "ManagerReassignedEvent": (
        (RealtimeChannel.REQUESTS.value, RealtimeChannel.MANAGERS.value, RealtimeChannel.DASHBOARD.value),
        ("manager_load", "active_requests", "recent_events"),
    ),
    "RequestCompletedEvent": (
        (RealtimeChannel.REQUESTS.value, RealtimeChannel.DASHBOARD.value),
        ("active_requests", "top_kpis", "recent_events"),
    ),
    "RequestOverdueEvent": (
        (RealtimeChannel.REQUESTS.value, RealtimeChannel.MANAGERS.value, RealtimeChannel.NOTIFICATIONS.value),
        ("sla_status", "manager_load", "recent_events"),
    ),
    "ManagerEscalationEvent": (
        (RealtimeChannel.MANAGERS.value, RealtimeChannel.NOTIFICATIONS.value, RealtimeChannel.AUDIT.value),
        ("manager_load", "recent_events", "recent_audit"),
    ),
    "SmartAssignmentCompletedEvent": (
        (RealtimeChannel.MANAGERS.value, RealtimeChannel.REQUESTS.value, RealtimeChannel.DASHBOARD.value),
        ("manager_load", "active_requests"),
    ),
    "ManagerAssignedEvent": (
        (RealtimeChannel.MANAGERS.value, RealtimeChannel.DASHBOARD.value),
        ("manager_load",),
    ),
    "ManagerReleasedEvent": (
        (RealtimeChannel.MANAGERS.value, RealtimeChannel.DASHBOARD.value),
        ("manager_load",),
    ),
    "ManagerUnavailableEvent": (
        (RealtimeChannel.MANAGERS.value, RealtimeChannel.HEALTH.value),
        ("manager_load", "system_status"),
    ),
    "ConfigurationChangedEvent": (
        (RealtimeChannel.CONFIGURATION.value, RealtimeChannel.DASHBOARD.value, RealtimeChannel.AUDIT.value),
        ("configuration_changes", "recent_audit"),
    ),
    "WorkflowStartedEvent": (
        (RealtimeChannel.WORKFLOWS.value, RealtimeChannel.DASHBOARD.value),
        ("workflow_status", "recent_events"),
    ),
    "WorkflowStepCompletedEvent": (
        (RealtimeChannel.WORKFLOWS.value,),
        ("workflow_status",),
    ),
    "WorkflowCompletedEvent": (
        (RealtimeChannel.WORKFLOWS.value, RealtimeChannel.DASHBOARD.value),
        ("workflow_status", "recent_events"),
    ),
    "WorkflowCancelledEvent": (
        (RealtimeChannel.WORKFLOWS.value, RealtimeChannel.DASHBOARD.value),
        ("workflow_status", "recent_events"),
    ),
}


class RealtimeEventDispatcher:
    """Bridges PlatformEventBus events into realtime channel broadcasts."""

    @staticmethod
    async def handle(event: BaseEvent) -> None:
        routing = _EVENT_ROUTING.get(event.event_type)
        if routing is None:
            return

        channels, widget_ids = routing
        event_data = event.to_dict()

        base_message = RealtimeMessage(
            type="event",
            event=event.event_type,
            data={"event": event_data},
            event_id=event.event_id,
        )

        widget_payloads = await RealtimeEventDispatcher._fetch_widgets(widget_ids)

        tasks = []
        for channel in channels:
            message = RealtimeMessage(
                type=base_message.type,
                channel=channel,
                event=base_message.event,
                data=dict(base_message.data),
                event_id=base_message.event_id,
            )
            if channel == RealtimeChannel.DASHBOARD.value and widget_payloads:
                message.data["widgets"] = widget_payloads
            tasks.append(realtime_hub.broadcast_channel(channel, message))

        if RealtimeChannel.AUDIT.value in channels:
            audit_message = RealtimeMessage(
                type="event",
                channel=RealtimeChannel.AUDIT.value,
                event="AuditEntry",
                data={"event": event_data, "source_event": event.event_type},
                event_id=event.event_id,
            )
            tasks.append(realtime_hub.broadcast_channel(RealtimeChannel.AUDIT.value, audit_message))

        await asyncio.gather(*tasks, return_exceptions=True)

    @staticmethod
    async def _fetch_widgets(widget_ids: tuple[str, ...]) -> dict[str, Any]:
        if not widget_ids:
            return {}

        from platform_operations.dashboard_service import operations_dashboard_service

        results = await asyncio.gather(
            *[
                operations_dashboard_service.fetch_widget(wid, use_cache=False)
                for wid in widget_ids
            ],
            return_exceptions=True,
        )

        payloads: dict[str, Any] = {}
        for wid, result in zip(widget_ids, results, strict=True):
            if isinstance(result, Exception):
                payloads[wid] = {"error": str(result)}
            else:
                payloads[wid] = result.to_dict()
        return payloads

    @staticmethod
    async def publish_health_changed(status: dict[str, Any]) -> None:
        message = RealtimeMessage(
            type="event",
            event="HealthChanged",
            data={"health": status},
        )
        await asyncio.gather(
            realtime_hub.broadcast_channel(RealtimeChannel.HEALTH.value, message),
            realtime_hub.broadcast_channel(RealtimeChannel.SYSTEM.value, message),
        )

    @staticmethod
    async def publish_plugin_loaded(plugin: dict[str, Any]) -> None:
        message = RealtimeMessage(
            type="event",
            event="PluginLoaded",
            data={"plugin": plugin},
        )
        await realtime_hub.broadcast_channel(RealtimeChannel.PLUGINS.value, message)

    @staticmethod
    async def publish_kpi_updated(kpi: dict[str, Any]) -> None:
        from platform_operations.dashboard_service import operations_dashboard_service

        widget = await operations_dashboard_service.fetch_widget("top_kpis", use_cache=False)
        message = RealtimeMessage(
            type="event",
            event="KPIUpdated",
            data={"kpi": kpi, "widget": widget.to_dict()},
        )
        await realtime_hub.broadcast_channel(RealtimeChannel.DASHBOARD.value, message)


def register_realtime_event_handlers() -> None:
    global _registered
    if _registered:
        return

    from events.event_bus import subscribe

    for event_name in _EVENT_ROUTING:
        subscribe(event_name, RealtimeEventDispatcher.handle, handler_id="realtime_dispatcher")

    _registered = True
    logger.info("realtime_event_handlers_registered count=%s", len(_EVENT_ROUTING))


def reset_realtime_event_handlers() -> None:
    global _registered
    _registered = False
