# Owner notification side effects for OwnerEscalationEvent.

from __future__ import annotations

from events.base_event import BaseEvent
from events.owner_events import OwnerEscalationEvent


class OwnerNotificationHandler:
    @staticmethod
    async def handle(event: BaseEvent) -> None:
        if isinstance(event, OwnerEscalationEvent):
            from services.owner_escalation_service import owner_escalation_service

            await owner_escalation_service.notify_owner(event)
