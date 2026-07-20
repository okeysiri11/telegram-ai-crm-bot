# Tool lifecycle events — integrated with PlatformEventBus.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class ToolStartedEvent(BaseEvent):
    tool_id: str
    execution_id: str
    agent_id: str | None = None
    user_id: str | None = None


@dataclass(kw_only=True)
class ToolCompletedEvent(BaseEvent):
    tool_id: str
    execution_id: str
    execution_time_ms: float = 0.0
    agent_id: str | None = None


@dataclass(kw_only=True)
class ToolFailedEvent(BaseEvent):
    tool_id: str
    execution_id: str
    error: str
    retries: int = 0
    agent_id: str | None = None
