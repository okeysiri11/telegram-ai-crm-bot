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


class SLAEventHandler:
    @staticmethod
    async def handle(event: BaseEvent) -> None:
        from services.pg_lead_sla_engine import LeadSlaEngineV1

        if isinstance(event, RequestCreatedEvent):
            await LeadSlaEngineV1.on_lead_created(
                client_request_id=uuid.UUID(event.request_id),
                request_number=event.request_number,
                manager_telegram_id=event.manager_telegram_id,
            )
        elif isinstance(event, RequestAssignedEvent):
            await LeadSlaEngineV1.on_assigned(
                request_number=event.request_number,
                manager_telegram_id=event.manager_telegram_id,
            )
        elif isinstance(event, RequestCompletedEvent):
            await LeadSlaEngineV1.on_closed(request_number=event.request_number)
        elif isinstance(event, RequestOverdueEvent):
            await LeadSlaEngineV1.raise_priority(event.request_number, priority="HIGH")
