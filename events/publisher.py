# Unified event publisher — every domain event passes PlatformEventBus.

from __future__ import annotations

from typing import Any

from events.base_event import BaseEvent
from events.event_bus import PlatformEventBus


async def publish(event: BaseEvent, *, wait: bool = False) -> dict[str, Any]:
    """Canonical publish entry point for all typed platform events."""
    return await PlatformEventBus.publish(event, wait=wait)


async def publish_ai(event: BaseEvent, *, wait: bool = False) -> dict[str, Any]:
    return await publish(event, wait=wait)


async def publish_skill(event: BaseEvent, *, wait: bool = False) -> dict[str, Any]:
    return await publish(event, wait=wait)


async def publish_workflow(event: BaseEvent, *, wait: bool = False) -> dict[str, Any]:
    return await publish(event, wait=wait)


async def publish_plugin(event: BaseEvent, *, wait: bool = False) -> dict[str, Any]:
    return await publish(event, wait=wait)


async def publish_notification(event: BaseEvent, *, wait: bool = False) -> dict[str, Any]:
    return await publish(event, wait=wait)


async def publish_sla(event: BaseEvent, *, wait: bool = False) -> dict[str, Any]:
    return await publish(event, wait=wait)
