# EventProvider — centralized EventBus publishing for verticals.

from __future__ import annotations

import logging
from typing import Any

from events.base_event import BaseEvent
from events.event_bus import publish

logger = logging.getLogger(__name__)


class EventProvider:
    @staticmethod
    async def publish(event: BaseEvent, *, wait: bool = False) -> dict[str, Any]:
        result = await publish(event, wait=wait)
        logger.debug(
            "sdk_event_published type=%s id=%s handlers=%s",
            event.event_type,
            event.event_id,
            result.get("handlers"),
        )
        return result

    @staticmethod
    async def publish_request_created(**fields: Any) -> dict[str, Any]:
        from events.request_events import RequestCreatedEvent

        return await EventProvider.publish(RequestCreatedEvent(**fields))

    @staticmethod
    async def publish_request_assigned(**fields: Any) -> dict[str, Any]:
        from events.request_events import RequestAssignedEvent

        return await EventProvider.publish(RequestAssignedEvent(**fields))

    @staticmethod
    async def publish_request_completed(**fields: Any) -> dict[str, Any]:
        from events.request_events import RequestCompletedEvent

        return await EventProvider.publish(RequestCompletedEvent(**fields))

    @staticmethod
    async def publish_request_overdue(**fields: Any) -> dict[str, Any]:
        from events.request_events import RequestOverdueEvent

        return await EventProvider.publish(RequestOverdueEvent(**fields))


event_provider = EventProvider()
