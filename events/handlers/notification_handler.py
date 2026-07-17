# Notification side effects for platform request events.

from __future__ import annotations

import logging

from events.base_event import BaseEvent
from events.request_events import (
    RequestAssignedEvent,
    RequestCreatedEvent,
    RequestOverdueEvent,
)

logger = logging.getLogger(__name__)


class NotificationEventHandler:
    @staticmethod
    async def handle(event: BaseEvent) -> None:
        if isinstance(event, RequestCreatedEvent):
            await NotificationEventHandler._on_created(event)
        elif isinstance(event, RequestAssignedEvent):
            await NotificationEventHandler._on_assigned(event)
        elif isinstance(event, RequestOverdueEvent):
            await NotificationEventHandler._on_overdue(event)

    @staticmethod
    async def _on_created(event: RequestCreatedEvent) -> None:
        from services.notification_service import notification_service

        await notification_service.notify_managers_new_request(
            vertical=event.vertical,
            request_number=event.request_number,
            client_name=event.client_name,
            product=event.description or event.request_type,
            manager_telegram_id=event.manager_telegram_id,
        )

    @staticmethod
    async def _on_assigned(event: RequestAssignedEvent) -> None:
        if event.manager_telegram_id is None:
            return
        from services.notification_service import notification_service

        await notification_service.notify_managers_new_request(
            vertical=event.vertical,
            request_number=event.request_number,
            client_name="",
            product=f"Assigned: {event.request_type}",
            manager_telegram_id=event.manager_telegram_id,
        )

    @staticmethod
    async def _on_overdue(event: RequestOverdueEvent) -> None:
        from services.notification_service import notification_service

        if event.manager_telegram_id is None:
            logger.info(
                "overdue_notification_skipped_no_manager",
                extra={"request_number": event.request_number},
            )
            return
        await notification_service.notify_managers_new_request(
            vertical=event.vertical,
            request_number=event.request_number,
            client_name="",
            product=f"⏰ Overdue ({event.overdue_seconds}s): {event.reason}",
            manager_telegram_id=event.manager_telegram_id,
        )
