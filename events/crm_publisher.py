# CRM outbox publisher — canonical import path for domain engines.

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

EventHandler = Callable[..., Awaitable[None] | None]


async def publish_crm_event(
    event_type: str,
    aggregate_type: str,
    aggregate_id: uuid.UUID,
    payload: dict[str, Any] | None = None,
    correlation_id: uuid.UUID | None = None,
    causation_id: uuid.UUID | None = None,
    *,
    session: AsyncSession | None = None,
) -> uuid.UUID:
    from services.crm_event_bus import publish_event

    return await publish_event(
        event_type,
        aggregate_type,
        aggregate_id,
        payload,
        correlation_id=correlation_id,
        causation_id=causation_id,
        session=session,
    )


def subscribe_crm_event(
    event_type: str,
    handler: EventHandler,
    *,
    handler_id: str | None = None,
) -> str:
    from services.crm_event_bus import subscribe

    return subscribe(event_type, handler, handler_id=handler_id)


async def get_crm_queue_size() -> dict[str, int]:
    from services.crm_event_bus import get_queue_size

    return await get_queue_size()
