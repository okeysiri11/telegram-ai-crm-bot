# Communication layer events — Sprint 7.2.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class ApplicationRegisteredEvent(BaseEvent):
    application_id: str = ""
    version: str = ""
    capabilities: list[str] = field(default_factory=list)


@dataclass(kw_only=True)
class ApplicationConnectedEvent(BaseEvent):
    application_id: str = ""
    health_status: str = ""


@dataclass(kw_only=True)
class EventPublishedEvent(BaseEvent):
    bus_event_id: str = ""
    event_name: str = ""
    category: str = ""
    source_application: str = ""


@dataclass(kw_only=True)
class EventConsumedEvent(BaseEvent):
    bus_event_id: str = ""
    consumer_application: str = ""
    topic: str = ""


@dataclass(kw_only=True)
class SynchronizationCompletedEvent(BaseEvent):
    sync_id: str = ""
    scope: str = ""
    source_application: str = ""
    target_count: int = 0


@dataclass(kw_only=True)
class MessageDeliveredEvent(BaseEvent):
    message_id: str = ""
    target_application: str = ""
    message_type: str = ""


@dataclass(kw_only=True)
class ContextSharedEvent(BaseEvent):
    context_id: str = ""
    user_id: str = ""
    source_application: str = ""
    shared_with: list[str] = field(default_factory=list)


@dataclass(kw_only=True)
class AgentDelegatedEvent(BaseEvent):
    task_type: str = ""
    source_application: str = ""
    target_agent: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
