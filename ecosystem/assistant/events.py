# Unified assistant events — Sprint 7.3.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class AssistantInvokedEvent(BaseEvent):
    user_id: str = ""
    conversation_id: str = ""
    application_id: str = ""
    message: str = ""


@dataclass(kw_only=True)
class IntentDetectedEvent(BaseEvent):
    user_id: str = ""
    intent: str = ""
    confidence: float = 0.0
    intent_label: str = ""


@dataclass(kw_only=True)
class SkillExecutedEvent(BaseEvent):
    skill_id: str = ""
    skill_name: str = ""
    user_id: str = ""
    result_status: str = ""


@dataclass(kw_only=True)
class KnowledgeUpdatedEvent(BaseEvent):
    node_id: str = ""
    action: str = ""
    application_id: str = ""


@dataclass(kw_only=True)
class ConversationCreatedEvent(BaseEvent):
    conversation_id: str = ""
    user_id: str = ""
    application_id: str = ""


@dataclass(kw_only=True)
class ContextRestoredEvent(BaseEvent):
    context_id: str = ""
    user_id: str = ""
    conversation_id: str = ""


@dataclass(kw_only=True)
class AgentRoutedEvent(BaseEvent):
    user_id: str = ""
    agent_id: str = ""
    intent: str = ""
    application_id: str = ""


@dataclass(kw_only=True)
class TaskCompletedEvent(BaseEvent):
    plan_id: str = ""
    user_id: str = ""
    goal: str = ""
    status: str = ""
    result: dict[str, Any] = field(default_factory=dict)
