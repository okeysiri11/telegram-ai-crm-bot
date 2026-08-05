"""Realtime fan-out for PlatformStateChangedEvent → RealtimeHub."""

from __future__ import annotations

import asyncio
import logging

from events.base_event import BaseEvent
from platform_realtime.models import RealtimeChannel, RealtimeMessage
from platform_realtime.realtime_hub import realtime_hub
from platform_state.audit import platform_state_audit
from platform_state.events import PlatformStateChangedEvent

logger = logging.getLogger(__name__)

_SLICE_CHANNEL: dict[str, str] = {
    "tasks": RealtimeChannel.DASHBOARD.value,
    "calendar": RealtimeChannel.DASHBOARD.value,
    "notifications": RealtimeChannel.NOTIFICATIONS.value,
    "conversations": RealtimeChannel.AI.value,
    "memory": RealtimeChannel.AI.value,
    "crm": RealtimeChannel.DASHBOARD.value,
    "files": RealtimeChannel.SYSTEM.value,
    "workspaces": RealtimeChannel.CONFIGURATION.value,
    "agents": RealtimeChannel.AI.value,
}


class PlatformStateRealtimeHandler:
    @staticmethod
    async def handle(event: BaseEvent) -> None:
        if not isinstance(event, PlatformStateChangedEvent):
            # Typed subclasses still carry PlatformStateChangedEvent fields
            if not hasattr(event, "slice_id"):
                return
        slice_id = getattr(event, "slice_id", "")
        channel = _SLICE_CHANNEL.get(slice_id, RealtimeChannel.SYSTEM.value)
        message = RealtimeMessage(
            type="event",
            channel=channel,
            event=event.event_type,
            data={
                "platform_state": True,
                "slice_id": slice_id,
                "entity_type": getattr(event, "entity_type", None),
                "entity_id": getattr(event, "entity_id", None),
                "action": getattr(event, "action", None),
                "revision": getattr(event, "revision", None),
                "source_client": getattr(event, "source_client", None),
                "payload": getattr(event, "payload", {}) or {},
            },
            event_id=event.event_id,
        )
        platform_state_audit.log(
            action=getattr(event, "action", "synced"),
            entity_type=getattr(event, "entity_type", "unknown"),
            entity_id=str(getattr(event, "entity_id", "")),
            actor_id=getattr(event, "actor_id", None),
            source_client=getattr(event, "source_client", None),
            after=getattr(event, "payload", None),
        )
        await asyncio.gather(
            realtime_hub.broadcast_channel(channel, message),
            realtime_hub.broadcast_channel(RealtimeChannel.SYSTEM.value, message),
            realtime_hub.broadcast_channel(RealtimeChannel.PLATFORM_STATE.value, message),
            return_exceptions=True,
        )


_PLATFORM_STATE_EVENT_NAMES = (
    "PlatformStateChangedEvent",
    "TaskCreatedEvent",
    "TaskCompletedEvent",
    "CalendarUpdatedEvent",
    "NotificationCreatedEvent",
    "ConversationUpdatedEvent",
    "MemoryUpdatedEvent",
    "CrmUpdatedEvent",
    "FileUploadedEvent",
    "WorkspaceChangedEvent",
)


def register_platform_state_handlers() -> None:
    from events.event_bus import subscribe

    for name in _PLATFORM_STATE_EVENT_NAMES:
        subscribe(name, PlatformStateRealtimeHandler.handle, handler_id="platform_state_realtime")
    logger.info("platform_state_handlers_registered count=%s", len(_PLATFORM_STATE_EVENT_NAMES))
