"""Enterprise Context Engine models — Sprint 36.4 (extends platform_memory SoR)."""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ContextSourceType(str, Enum):
    USER_PROFILE = "user_profile"
    ORGANIZATION = "organization"
    PROJECT = "project"
    WORKSPACE = "workspace"
    DOCUMENTS = "documents"
    KNOWLEDGE_BASE = "knowledge_base"
    WORKFLOW_STATE = "workflow_state"
    CONVERSATION_HISTORY = "conversation_history"
    AGENT_MEMORY = "agent_memory"
    RUNTIME_VARIABLES = "runtime_variables"


class SensitivityLevel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class Visibility(str, Enum):
    GLOBAL = "global"
    TENANT = "tenant"
    WORKSPACE = "workspace"
    USER = "user"
    SESSION = "session"


SOURCE_RANK: dict[str, int] = {
    ContextSourceType.RUNTIME_VARIABLES.value: 100,
    ContextSourceType.CONVERSATION_HISTORY.value: 90,
    ContextSourceType.AGENT_MEMORY.value: 80,
    ContextSourceType.WORKFLOW_STATE.value: 75,
    ContextSourceType.USER_PROFILE.value: 70,
    ContextSourceType.PROJECT.value: 65,
    ContextSourceType.WORKSPACE.value: 60,
    ContextSourceType.ORGANIZATION.value: 55,
    ContextSourceType.DOCUMENTS.value: 50,
    ContextSourceType.KNOWLEDGE_BASE.value: 45,
}


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass
class ContextFragment:
    fragment_id: str
    source: ContextSourceType | str
    key: str
    content: str
    priority: int = 0
    tokens: int = 0
    sensitivity: SensitivityLevel | str = SensitivityLevel.INTERNAL
    visibility: Visibility | str = Visibility.TENANT
    expires_at: float | None = None
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0

    def __post_init__(self) -> None:
        if isinstance(self.source, str):
            self.source = ContextSourceType(self.source)
        if isinstance(self.sensitivity, str):
            self.sensitivity = SensitivityLevel(self.sensitivity)
        if isinstance(self.visibility, str):
            self.visibility = Visibility(self.visibility)
        if not self.tokens:
            self.tokens = max(1, len(self.content) // 4)
        if not self.priority:
            src = self.source.value if isinstance(self.source, ContextSourceType) else str(self.source)
            self.priority = SOURCE_RANK.get(src, 10)

    def to_dict(self) -> dict[str, Any]:
        return {
            "fragment_id": self.fragment_id,
            "source": self.source.value if isinstance(self.source, ContextSourceType) else self.source,
            "key": self.key,
            "content": self.content,
            "priority": self.priority,
            "tokens": self.tokens,
            "sensitivity": self.sensitivity.value if isinstance(self.sensitivity, SensitivityLevel) else self.sensitivity,
            "visibility": self.visibility.value if isinstance(self.visibility, Visibility) else self.visibility,
            "expires_at": self.expires_at,
            "version": self.version,
            "metadata": dict(self.metadata),
            "score": self.score,
        }


@dataclass
class ContextNode:
    node_id: str
    label: str
    source: str
    fragment_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ContextEdge:
    edge_id: str
    from_id: str
    to_id: str
    relation: str = "related"
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ContextGraph:
    nodes: list[ContextNode] = field(default_factory=list)
    edges: list[ContextEdge] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
        }


@dataclass
class ContextPermission:
    permission_id: str
    principal: str
    source: str
    action: str = "read"  # read | write | deny
    max_sensitivity: SensitivityLevel | str = SensitivityLevel.INTERNAL
    isolation_key: str | None = None
    version: int = 1

    def __post_init__(self) -> None:
        if isinstance(self.max_sensitivity, str):
            self.max_sensitivity = SensitivityLevel(self.max_sensitivity)

    def to_dict(self) -> dict[str, Any]:
        return {
            "permission_id": self.permission_id,
            "principal": self.principal,
            "source": self.source,
            "action": self.action,
            "max_sensitivity": (
                self.max_sensitivity.value
                if isinstance(self.max_sensitivity, SensitivityLevel)
                else self.max_sensitivity
            ),
            "isolation_key": self.isolation_key,
            "version": self.version,
        }


@dataclass
class ContextSession:
    session_id: str
    user_id: str | None = None
    tenant_id: str | None = None
    workspace_id: str | None = None
    principal: str = "system"
    status: str = "active"
    fragment_ids: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    expires_at: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ContextCacheEntry:
    cache_key: str
    bundle: dict[str, Any]
    created_at: float = field(default_factory=time.time)
    expires_at: float | None = None
    hits: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "cache_key": self.cache_key,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "hits": self.hits,
            "token_count": self.bundle.get("total_tokens", 0),
        }


@dataclass
class ContextHistoryEntry:
    history_id: str
    session_id: str | None
    action: str
    details: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ContextBundle:
    bundle_id: str
    session_id: str | None
    fragments: list[ContextFragment]
    prompt_context: str
    total_tokens: int
    truncated: bool = False
    cached: bool = False
    graph: ContextGraph | None = None
    sources_used: list[str] = field(default_factory=list)
    filtered_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "session_id": self.session_id,
            "fragments": [f.to_dict() for f in self.fragments],
            "prompt_context": self.prompt_context,
            "total_tokens": self.total_tokens,
            "truncated": self.truncated,
            "cached": self.cached,
            "graph": self.graph.to_dict() if self.graph else None,
            "sources_used": list(self.sources_used),
            "filtered_count": self.filtered_count,
            "metadata": dict(self.metadata),
        }
