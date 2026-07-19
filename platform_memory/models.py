# Platform Memory — domain models.

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class MemoryCategory(str, Enum):
    CONVERSATION = "conversation"
    USER_FACT = "user_fact"
    BUSINESS_FACT = "business_fact"
    LONG_TERM = "long_term"
    SESSION = "session"
    PROJECT = "project"
    AGENT = "agent"


class ConversationRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass(frozen=True)
class ConversationTurn:
    turn_id: str
    session_id: str
    role: str
    content: str
    user_id: str | None = None
    agent_id: str | None = None
    plugin_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "plugin_id": self.plugin_id,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class UserFact:
    fact_id: str
    user_id: str
    key: str
    value: str
    source: str = "explicit"
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "user_id": self.user_id,
            "key": self.key,
            "value": self.value,
            "source": self.source,
            "metadata": self.metadata,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class BusinessFact:
    fact_id: str
    organization_id: str
    key: str
    value: str
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "organization_id": self.organization_id,
            "key": self.key,
            "value": self.value,
            "metadata": self.metadata,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class AgentMemoryRecord:
    memory_id: str
    agent_id: str
    content: str
    memory_key: str = ""
    user_id: str | None = None
    session_id: str | None = None
    category: str = MemoryCategory.AGENT.value
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "agent_id": self.agent_id,
            "content": self.content,
            "memory_key": self.memory_key,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "category": self.category,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class SessionMemoryRecord:
    memory_id: str
    session_id: str
    content: str
    memory_key: str = ""
    user_id: str | None = None
    agent_id: str | None = None
    expires_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "session_id": self.session_id,
            "content": self.content,
            "memory_key": self.memory_key,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "expires_at": self.expires_at,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class ProjectMemoryRecord:
    memory_id: str
    project_id: str
    content: str
    memory_key: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "project_id": self.project_id,
            "content": self.content,
            "memory_key": self.memory_key,
            "metadata": self.metadata,
            "updated_at": self.updated_at,
        }


@dataclass
class ContextAssemblyRequest:
    session_id: str | None = None
    user_id: str | None = None
    agent_id: str | None = None
    plugin_id: str | None = None
    organization_id: str | None = None
    project_id: str | None = None
    current_message: str | None = None
    query: str | None = None
    configuration: dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextAssemblyResult:
    prompt_context: str
    sections: dict[str, Any]
    total_tokens: int
    summarized: bool = False
    conversation_turn_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_context": self.prompt_context,
            "sections": self.sections,
            "total_tokens": self.total_tokens,
            "summarized": self.summarized,
            "conversation_turn_count": self.conversation_turn_count,
        }


@dataclass
class AIContextBundle:
    """Injected into AI Skill and Workflow execution."""

    relevant_memory: list[dict[str, Any]] = field(default_factory=list)
    relevant_knowledge: list[dict[str, Any]] = field(default_factory=list)
    conversation_history: list[dict[str, Any]] = field(default_factory=list)
    plugin_context: dict[str, Any] = field(default_factory=dict)
    configuration: dict[str, Any] = field(default_factory=dict)
    user_profile: list[dict[str, Any]] = field(default_factory=list)
    business_facts: list[dict[str, Any]] = field(default_factory=list)
    project_memory: list[dict[str, Any]] = field(default_factory=list)
    session_memory: list[dict[str, Any]] = field(default_factory=list)
    prompt_context: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "relevant_memory": self.relevant_memory,
            "relevant_knowledge": self.relevant_knowledge,
            "conversation_history": self.conversation_history,
            "plugin_context": self.plugin_context,
            "configuration": self.configuration,
            "user_profile": self.user_profile,
            "business_facts": self.business_facts,
            "project_memory": self.project_memory,
            "session_memory": self.session_memory,
            "prompt_context": self.prompt_context,
        }


def new_id() -> str:
    return str(uuid4())
