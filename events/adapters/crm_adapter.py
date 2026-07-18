# CRM EventBus adapter — CRM outbox events pass through PlatformEventBus.

from __future__ import annotations

import logging
import uuid
from typing import Any

from events.event_bus import PlatformEventBus
from events.generic_events import GenericPlatformEvent

logger = logging.getLogger(__name__)


async def publish_crm_to_platform_bus(
    event_type: str,
    aggregate_type: str,
    aggregate_id: uuid.UUID,
    payload: dict[str, Any] | None = None,
    *,
    correlation_id: uuid.UUID | None = None,
    causation_id: uuid.UUID | None = None,
    crm_event_id: uuid.UUID | None = None,
    wait: bool = False,
) -> dict[str, Any]:
    """Publish CRM event through canonical PlatformEventBus before outbox persistence."""
    generic = GenericPlatformEvent.from_crm(
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload=payload,
        correlation_id=correlation_id,
        causation_id=causation_id,
        crm_event_id=crm_event_id,
    )
    result = await PlatformEventBus.publish(generic, wait=wait)
    logger.debug(
        "crm_event_routed_to_platform_bus",
        extra={"event_type": event_type, "aggregate_id": str(aggregate_id)},
    )
    return result
