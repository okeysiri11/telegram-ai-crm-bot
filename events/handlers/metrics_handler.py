# Metrics side effects for platform request events.

from __future__ import annotations

from events.base_event import BaseEvent
from events.request_events import (
    ManagerReassignedEvent,
    RequestAssignedEvent,
    RequestCompletedEvent,
    RequestCreatedEvent,
)


class MetricsEventHandler:
    @staticmethod
    async def handle(event: BaseEvent) -> None:
        from services.platform_metrics_service import platform_metrics_service

        if isinstance(event, RequestCreatedEvent):
            await platform_metrics_service.track_request_created(
                request_number=event.request_number,
                request_type=event.request_type,
                status=event.status,
                vertical=event.vertical,
                request_id=event.request_id,
                manager_id=event.manager_id,
                client_telegram_id=event.client_telegram_id,
            )
        elif isinstance(event, RequestAssignedEvent):
            await platform_metrics_service.track_manager_assigned(
                request_number=event.request_number,
                manager_id=event.manager_id,
            )
        elif isinstance(event, RequestCompletedEvent):
            await platform_metrics_service.track_request_closed(
                request_number=event.request_number,
                status=event.status,
                converted_to_deal=event.converted_to_deal,
            )
        elif isinstance(event, ManagerReassignedEvent):
            await platform_metrics_service.track_manager_assigned(
                request_number=event.request_number,
                manager_id=event.manager_id,
            )
