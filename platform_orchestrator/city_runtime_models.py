"""Enterprise City Runtime models — Sprint 37.0 (extends platform_orchestrator SoR)."""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class HealthLevel(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"


class WorkspaceModule(str, Enum):
    CRM = "crm"
    ERP = "erp"
    AI_RUNTIME = "ai_runtime"
    MULTI_AGENT = "multi_agent_runtime"
    PROJECT_MEMORY = "project_memory"
    CONTEXT_ENGINE = "context_engine"
    WORKFLOW = "workflow_runtime"
    CREATIVE_FACTORY = "creative_factory"
    VOICE = "voice_runtime"
    ANALYTICS = "analytics"
    KNOWLEDGE = "knowledge_base"
    SKILLS_SDK = "skills_sdk"
    EVENT_BUS = "event_bus"
    SERVICE_BUILDER = "service_builder"


class SearchKind(str, Enum):
    CLIENT = "clients"
    PROJECT = "projects"
    DOCUMENT = "documents"
    TASK = "tasks"
    WORKFLOW = "workflows"
    MEMORY = "memories"
    AGENT = "agents"
    MEDIA = "media"
    REPORT = "reports"
    SERVICE = "services"
    COMMAND = "commands"


class CommandKind(str, Enum):
    NATURAL = "natural_language"
    VOICE = "voice"
    AI = "ai_execution"
    WORKFLOW = "workflow_execution"
    SERVICE = "service_execution"


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass
class PlatformServiceEntry:
    service_id: str
    name: str
    display_name: str
    route: str
    category: str
    status: HealthLevel | str = HealthLevel.HEALTHY
    sprint: str = ""
    api_prefixes: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.status, str):
            self.status = HealthLevel(self.status)

    def to_dict(self) -> dict[str, Any]:
        return {
            "service_id": self.service_id,
            "name": self.name,
            "display_name": self.display_name,
            "route": self.route,
            "category": self.category,
            "status": self.status.value if isinstance(self.status, HealthLevel) else self.status,
            "sprint": self.sprint,
            "api_prefixes": list(self.api_prefixes),
            "dependencies": list(self.dependencies),
            "metadata": dict(self.metadata),
        }


@dataclass
class PlatformSession:
    session_id: str
    user_id: str
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    shared_context: dict[str, Any] = field(default_factory=dict)
    shared_memory: dict[str, Any] = field(default_factory=dict)
    active_module: str | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PlatformMetric:
    metric_id: str
    name: str
    value: float
    unit: str = ""
    category: str = "kpi"
    labels: dict[str, str] = field(default_factory=dict)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HealthRecord:
    component_id: str
    name: str
    level: HealthLevel | str = HealthLevel.HEALTHY
    message: str = ""
    latency_ms: float = 0.0
    checked_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.level, str):
            self.level = HealthLevel(self.level)

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_id": self.component_id,
            "name": self.name,
            "level": self.level.value if isinstance(self.level, HealthLevel) else self.level,
            "message": self.message,
            "latency_ms": self.latency_ms,
            "checked_at": self.checked_at,
            "metadata": dict(self.metadata),
        }


@dataclass
class UsageEvent:
    usage_id: str
    action: str
    module: str
    user_id: str = "system"
    details: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PlatformConfig:
    key: str
    value: Any
    category: str = "general"
    description: str = ""
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SearchHit:
    hit_id: str
    kind: SearchKind | str
    title: str
    route: str
    score: float
    snippet: str = ""
    module: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.kind, str):
            self.kind = SearchKind(self.kind)

    def to_dict(self) -> dict[str, Any]:
        return {
            "hit_id": self.hit_id,
            "kind": self.kind.value if isinstance(self.kind, SearchKind) else self.kind,
            "title": self.title,
            "route": self.route,
            "score": self.score,
            "snippet": self.snippet,
            "module": self.module,
            "metadata": dict(self.metadata),
        }


@dataclass
class NotificationItem:
    notification_id: str
    title: str
    body: str = ""
    level: str = "info"
    module: str = "platform"
    read: bool = False
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CommandResult:
    command_id: str
    kind: CommandKind | str
    input_text: str
    intent: str
    status: str = "completed"
    actions: list[dict[str, Any]] = field(default_factory=list)
    result: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if isinstance(self.kind, str):
            self.kind = CommandKind(self.kind)

    def to_dict(self) -> dict[str, Any]:
        return {
            "command_id": self.command_id,
            "kind": self.kind.value if isinstance(self.kind, CommandKind) else self.kind,
            "input_text": self.input_text,
            "intent": self.intent,
            "status": self.status,
            "actions": list(self.actions),
            "result": dict(self.result),
            "created_at": self.created_at,
        }


@dataclass
class ActivityItem:
    activity_id: str
    action: str
    module: str
    summary: str
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
