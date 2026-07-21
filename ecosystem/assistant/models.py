# Assistant models — Sprint 7.3.

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


def _id() -> str:
    return str(uuid.uuid4())


def _ts() -> float:
    return time.time()


class IntentType(str, enum.Enum):
    GENERAL = "general"
    APPLICATION = "application"
    AGENT = "agent"
    TOOL = "tool"
    WORKFLOW = "workflow"
    KNOWLEDGE = "knowledge"
    TASK = "task"


class SkillType(str, enum.Enum):
    APPLICATION = "application"
    WORKFLOW = "workflow"
    TOOL = "tool"
    AGENT = "agent"


class RouteTarget(str, enum.Enum):
    APPLICATION = "application"
    AGENT = "agent"
    TOOL = "tool"
    WORKFLOW = "workflow"
    FALLBACK = "fallback"


@dataclass
class ConversationTurn:
    turn_id: str = field(default_factory=_id)
    role: str = "user"
    content: str = ""
    locale: str = "en"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "role": self.role,
            "content": self.content,
            "locale": self.locale,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class Conversation:
    conversation_id: str = field(default_factory=_id)
    user_id: str = ""
    application_id: str = ""
    organization_id: str = ""
    title: str = ""
    turns: list[ConversationTurn] = field(default_factory=list)
    summary: str = ""
    locale: str = "en"
    voice_ready: bool = False
    is_active: bool = True
    context_snapshot: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "application_id": self.application_id,
            "organization_id": self.organization_id,
            "title": self.title,
            "turns": [t.to_dict() for t in self.turns],
            "summary": self.summary,
            "locale": self.locale,
            "voice_ready": self.voice_ready,
            "is_active": self.is_active,
            "context_snapshot": dict(self.context_snapshot),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class KnowledgeNode:
    node_id: str = field(default_factory=_id)
    label: str = ""
    node_type: str = "concept"
    application_id: str = ""
    content: str = ""
    tags: list[str] = field(default_factory=list)
    embedding_hint: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "label": self.label,
            "node_type": self.node_type,
            "application_id": self.application_id,
            "content": self.content,
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class KnowledgeEdge:
    edge_id: str = field(default_factory=_id)
    source_id: str = ""
    target_id: str = ""
    relation: str = "related_to"
    weight: float = 1.0
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation,
            "weight": self.weight,
            "created_at": self.created_at,
        }


@dataclass
class MemoryEntry:
    memory_id: str = field(default_factory=_id)
    user_id: str = ""
    application_id: str = ""
    content: str = ""
    memory_type: str = "episodic"
    tags: list[str] = field(default_factory=list)
    importance: float = 0.5
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "user_id": self.user_id,
            "application_id": self.application_id,
            "content": self.content,
            "memory_type": self.memory_type,
            "tags": list(self.tags),
            "importance": self.importance,
            "created_at": self.created_at,
        }


@dataclass
class ContextBundle:
    context_id: str = field(default_factory=_id)
    user_id: str = ""
    global_context: dict[str, Any] = field(default_factory=dict)
    application_context: dict[str, Any] = field(default_factory=dict)
    user_context: dict[str, Any] = field(default_factory=dict)
    organization_context: dict[str, Any] = field(default_factory=dict)
    conversation_context: dict[str, Any] = field(default_factory=dict)
    task_context: dict[str, Any] = field(default_factory=dict)
    updated_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_id": self.context_id,
            "user_id": self.user_id,
            "global_context": dict(self.global_context),
            "application_context": dict(self.application_context),
            "user_context": dict(self.user_context),
            "organization_context": dict(self.organization_context),
            "conversation_context": dict(self.conversation_context),
            "task_context": dict(self.task_context),
            "updated_at": self.updated_at,
        }


@dataclass
class Skill:
    skill_id: str = field(default_factory=_id)
    name: str = ""
    skill_type: SkillType = SkillType.APPLICATION
    description: str = ""
    application_id: str = ""
    handler_key: str = ""
    parameters_schema: dict[str, Any] = field(default_factory=dict)
    is_enabled: bool = True
    priority: int = 100
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "skill_type": self.skill_type.value,
            "description": self.description,
            "application_id": self.application_id,
            "handler_key": self.handler_key,
            "parameters_schema": dict(self.parameters_schema),
            "is_enabled": self.is_enabled,
            "priority": self.priority,
            "created_at": self.created_at,
        }


@dataclass
class RoutingDecision:
    decision_id: str = field(default_factory=_id)
    intent: IntentType = IntentType.GENERAL
    intent_label: str = ""
    confidence: float = 0.0
    target_type: RouteTarget = RouteTarget.FALLBACK
    target_id: str = ""
    application_id: str = ""
    agent_id: str = ""
    tool_id: str = ""
    workflow_id: str = ""
    priority: int = 100
    fallback_used: bool = False
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "intent": self.intent.value,
            "intent_label": self.intent_label,
            "confidence": self.confidence,
            "target_type": self.target_type.value,
            "target_id": self.target_id,
            "application_id": self.application_id,
            "agent_id": self.agent_id,
            "tool_id": self.tool_id,
            "workflow_id": self.workflow_id,
            "priority": self.priority,
            "fallback_used": self.fallback_used,
            "created_at": self.created_at,
        }


@dataclass
class TaskPlan:
    plan_id: str = field(default_factory=_id)
    user_id: str = ""
    goal: str = ""
    steps: list[dict[str, Any]] = field(default_factory=list)
    status: str = "planned"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "user_id": self.user_id,
            "goal": self.goal,
            "steps": list(self.steps),
            "status": self.status,
            "created_at": self.created_at,
        }


@dataclass
class AssistantResponse:
    response_id: str = field(default_factory=_id)
    conversation_id: str = ""
    reply: str = ""
    intent: str = ""
    routing: dict[str, Any] = field(default_factory=dict)
    skills_executed: list[str] = field(default_factory=list)
    plan: dict[str, Any] | None = None
    knowledge_hits: list[dict[str, Any]] = field(default_factory=list)
    locale: str = "en"
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "response_id": self.response_id,
            "conversation_id": self.conversation_id,
            "reply": self.reply,
            "intent": self.intent,
            "routing": dict(self.routing),
            "skills_executed": list(self.skills_executed),
            "plan": self.plan,
            "knowledge_hits": list(self.knowledge_hits),
            "locale": self.locale,
            "created_at": self.created_at,
        }
