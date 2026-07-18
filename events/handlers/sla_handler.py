# SLA side effects for platform request events.

from __future__ import annotations

import uuid

from events.base_event import BaseEvent
from events.request_events import (
    RequestAssignedEvent,
    RequestCompletedEvent,
    RequestCreatedEvent,
    RequestOverdueEvent,
)
from platform_legacy import legacy


class SLAEventHandler:
    @staticmethod
    async def handle(event: BaseEvent) -> None:
        if isinstance(event, RequestCreatedEvent):
            await legacy.sla.on_lead_created(
                client_request_id=uuid.UUID(event.request_id),
                request_number=event.request_number,
                manager_telegram_id=event.manager_telegram_id,
            )
        elif isinstance(event, RequestAssignedEvent):
            await legacy.sla.on_assigned(
                request_number=event.request_number,
                manager_telegram_id=event.manager_telegram_id,
            )
        elif isinstance(event, RequestCompletedEvent):
            await legacy.sla.on_closed(request_number=event.request_number)
        elif isinstance(event, RequestOverdueEvent):
            await legacy.sla.raise_priority(event.request_number, priority="HIGH")
