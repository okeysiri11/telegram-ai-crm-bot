# Platform Memory — domain events.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class MemoryStoredEvent(BaseEvent):
    memory_id: str = ""
    category: str = ""
    agent_id: str = ""


@dataclass(kw_only=True)
class ConversationAppendedEvent(BaseEvent):
    session_id: str = ""
    turn_id: str = ""
    role: str = ""


@dataclass(kw_only=True)
class ContextAssembledEvent(BaseEvent):
    session_id: str = ""
    total_tokens: int = 0
    summarized: bool = False


@dataclass(kw_only=True)
class UserFactStoredEvent(BaseEvent):
    user_id: str = ""
    key: str = ""
