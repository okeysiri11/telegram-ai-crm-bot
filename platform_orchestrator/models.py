# Orchestrator domain models.

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AgentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEGRADED = "degraded"
    SHUTTING_DOWN = "shutting_down"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class MessageType(str, Enum):
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    EVENT = "event"


@dataclass(frozen=True)
class AgentMetadata:
    id: str
    name: str
    description: str
    capabilities: tuple[str, ...]
    priority: int
    version: str
    status: AgentStatus = AgentStatus.ACTIVE


@dataclass
class AgentHealthResult:
    agent_id: str
    status: str
    healthy: bool
    details: dict[str, Any] = field(default_factory=dict)
    checked_at: float = field(default_factory=time.time)


@dataclass
class AgentContext:
    """Injected context — agents must not access global state directly."""

    user_context: dict[str, Any] = field(default_factory=dict)
    memory_context: dict[str, Any] = field(default_factory=dict)
    session_context: dict[str, Any] = field(default_factory=dict)
    platform_context: dict[str, Any] = field(default_factory=dict)
    permissions: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "user_context": dict(self.user_context),
            "memory_context": dict(self.memory_context),
            "session_context": dict(self.session_context),
            "platform_context": dict(self.platform_context),
            "permissions": list(self.permissions),
        }


@dataclass
class TaskRequest:
    capability: str
    payload: dict[str, Any] = field(default_factory=dict)
    context: AgentContext = field(default_factory=AgentContext)
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timeout_seconds: float | None = None
    max_retries: int | None = None
    fallback_capability: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    task_id: str
    agent_id: str
    capability: str
    status: TaskStatus
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    error_code: str | None = None
    retries: int = 0
    execution_time_ms: float = 0.0
    routing_decision: dict[str, Any] = field(default_factory=dict)
    preserved_context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.status == TaskStatus.COMPLETED


@dataclass(frozen=True)
class RoutingDecision:
    capability: str
    agent_id: str
    agent_name: str
    priority: int
    reason: str
    candidates: tuple[str, ...] = ()


@dataclass
class AgentMessage:
    message_type: MessageType
    source_agent_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    target_agent_id: str | None = None
    correlation_id: str | None = None
    timestamp: float = field(default_factory=time.time)
