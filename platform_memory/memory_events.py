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


# Epic 45.2 — continuous memory events


@dataclass(kw_only=True)
class ContinuousMemorySavedEvent(BaseEvent):
    memory_id: str = ""
    level: str = ""
    owner_id: str = ""


@dataclass(kw_only=True)
class SmartRecallEvent(BaseEvent):
    owner_id: str = ""
    intent: str = ""


@dataclass(kw_only=True)
class AiResumeBuiltEvent(BaseEvent):
    owner_id: str = ""
    unfinished: int = 0


@dataclass(kw_only=True)
class MemoryTimelineEvent(BaseEvent):
    owner_id: str = ""
    action: str = ""
    title: str = ""
