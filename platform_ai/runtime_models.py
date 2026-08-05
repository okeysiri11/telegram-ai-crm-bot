"""AI Runtime domain models — Sprint 36.3 (extends platform_ai SoR)."""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ToolPermission(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    ASK = "ask"


@dataclass
class RuntimeContext:
    session_id: str
    user_id: str | None = None
    tenant_id: str | None = None
    messages: list[dict[str, Any]] = field(default_factory=list)
    memory: dict[str, Any] = field(default_factory=dict)
    tools_enabled: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    sandbox_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AIRuntimeSession:
    session_id: str
    status: SessionStatus | str = SessionStatus.ACTIVE
    provider_id: str | None = None
    model_id: str | None = None
    context: RuntimeContext | None = None
    request_count: int = 0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    finished_at: float | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.status, str):
            self.status = SessionStatus(self.status)
        if self.context is None:
            self.context = RuntimeContext(session_id=self.session_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "status": self.status.value if isinstance(self.status, SessionStatus) else self.status,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "context": self.context.to_dict() if self.context else {},
            "request_count": self.request_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "finished_at": self.finished_at,
            "error": self.error,
        }


@dataclass
class PromptVersionRecord:
    template_id: str
    version: int
    body: str
    system_prompt: str = ""
    variables: list[str] = field(default_factory=list)
    changelog: str = ""
    created_at: float = field(default_factory=time.time)
    is_active: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ToolDefinition:
    tool_id: str
    name: str
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    permission: ToolPermission | str = ToolPermission.ALLOW
    mcp_compatible: bool = True
    timeout_sec: float = 30.0
    sandbox: bool = True
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.permission, str):
            self.permission = ToolPermission(self.permission)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "description": self.description,
            "parameters": dict(self.parameters),
            "permission": self.permission.value if isinstance(self.permission, ToolPermission) else self.permission,
            "mcp_compatible": self.mcp_compatible,
            "timeout_sec": self.timeout_sec,
            "sandbox": self.sandbox,
            "enabled": self.enabled,
            "metadata": dict(self.metadata),
            "function_schema": {
                "type": "function",
                "function": {
                    "name": self.name,
                    "description": self.description,
                    "parameters": self.parameters or {"type": "object", "properties": {}},
                },
            },
        }


@dataclass
class ToolExecutionRecord:
    execution_id: str
    tool_id: str
    session_id: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)
    result: Any = None
    success: bool = True
    error: str | None = None
    duration_ms: float = 0.0
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AIRuntimeLog:
    log_id: str
    level: str
    message: str
    session_id: str | None = None
    provider_id: str | None = None
    model_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"
