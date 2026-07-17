# Audit side effects for platform request events.

from __future__ import annotations

from events.base_event import BaseEvent
from events.request_events import (
    ManagerReassignedEvent,
    RequestAssignedEvent,
    RequestCompletedEvent,
    RequestCreatedEvent,
)


class AuditEventHandler:
    @staticmethod
    async def handle(event: BaseEvent) -> None:
        from services.pg_platform_audit_engine import PlatformAuditEngineV1

        if isinstance(event, RequestCreatedEvent):
            await PlatformAuditEngineV1.lead_created(
                event.request_id,
                user_id=event.client_telegram_id,
                request_number=event.request_number,
                vertical=event.vertical,
                request_type=event.request_type,
            )
        elif isinstance(event, RequestAssignedEvent):
            await PlatformAuditEngineV1.manager_assigned(
                event.request_id,
                user_id=event.manager_telegram_id,
                request_number=event.request_number,
                manager_id=event.manager_id,
            )
        elif isinstance(event, RequestCompletedEvent):
            await PlatformAuditEngineV1.status_changed(
                event.request_id,
                user_id=event.client_telegram_id,
                request_number=event.request_number,
                status=event.status,
            )
        elif isinstance(event, ManagerReassignedEvent):
            await PlatformAuditEngineV1.manager_assigned(
                event.request_id,
                user_id=event.manager_telegram_id,
                request_number=event.request_number,
                manager_id=event.manager_id,
                previous_manager_id=event.previous_manager_id,
                reassigned=True,
            )
