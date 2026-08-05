"""Platform state domain events — published on PlatformEventBus only."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class PlatformStateChangedEvent(BaseEvent):
    slice_id: str
    entity_type: str
    entity_id: str
    action: str  # created | updated | deleted | synced
    revision: str
    source_client: str | None = None
    actor_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    version: int = 1


# Named aliases matching sprint event vocabulary (same bus, typed convenience).
@dataclass(kw_only=True)
class TaskCreatedEvent(PlatformStateChangedEvent):
    slice_id: str = "tasks"
    entity_type: str = "task"
    action: str = "created"


@dataclass(kw_only=True)
class TaskCompletedEvent(PlatformStateChangedEvent):
    slice_id: str = "tasks"
    entity_type: str = "task"
    action: str = "updated"


@dataclass(kw_only=True)
class CalendarUpdatedEvent(PlatformStateChangedEvent):
    slice_id: str = "calendar"
    entity_type: str = "calendar_event"
    action: str = "updated"


@dataclass(kw_only=True)
class NotificationCreatedEvent(PlatformStateChangedEvent):
    slice_id: str = "notifications"
    entity_type: str = "notification"
    action: str = "created"


@dataclass(kw_only=True)
class ConversationUpdatedEvent(PlatformStateChangedEvent):
    slice_id: str = "conversations"
    entity_type: str = "conversation"
    action: str = "updated"


@dataclass(kw_only=True)
class MemoryUpdatedEvent(PlatformStateChangedEvent):
    slice_id: str = "memory"
    entity_type: str = "memory"
    action: str = "updated"


@dataclass(kw_only=True)
class CrmUpdatedEvent(PlatformStateChangedEvent):
    slice_id: str = "crm"
    entity_type: str = "crm"
    action: str = "updated"


@dataclass(kw_only=True)
class FileUploadedEvent(PlatformStateChangedEvent):
    slice_id: str = "files"
    entity_type: str = "file"
    action: str = "created"


@dataclass(kw_only=True)
class WorkspaceChangedEvent(PlatformStateChangedEvent):
    slice_id: str = "workspaces"
    entity_type: str = "workspace"
    action: str = "updated"
