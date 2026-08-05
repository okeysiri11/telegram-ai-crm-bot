"""Project Memory Engine models — Sprint 36.5 (extends platform_memory SoR)."""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class MemoryKind(str, Enum):
    PROJECT = "project"
    AGENT = "agent"
    CLIENT = "client"
    WORKFLOW = "workflow"
    DOCUMENT = "document"


class MemoryLayer(str, Enum):
    SHORT_TERM = "short_term"
    WORKING = "working"
    LONG_TERM = "long_term"
    SHARED_TEAM = "shared_team"


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass
class MemoryRecord:
    memory_id: str
    kind: MemoryKind | str
    layer: MemoryLayer | str = MemoryLayer.LONG_TERM
    title: str = ""
    content: str = ""
    project_id: str | None = None
    agent_id: str | None = None
    client_id: str | None = None
    workflow_id: str | None = None
    document_id: str | None = None
    tags: list[str] = field(default_factory=list)
    importance: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    expires_at: float | None = None

    def __post_init__(self) -> None:
        if isinstance(self.kind, str):
            self.kind = MemoryKind(self.kind)
        if isinstance(self.layer, str):
            self.layer = MemoryLayer(self.layer)

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "kind": self.kind.value if isinstance(self.kind, MemoryKind) else self.kind,
            "layer": self.layer.value if isinstance(self.layer, MemoryLayer) else self.layer,
            "title": self.title,
            "content": self.content,
            "project_id": self.project_id,
            "agent_id": self.agent_id,
            "client_id": self.client_id,
            "workflow_id": self.workflow_id,
            "document_id": self.document_id,
            "tags": list(self.tags),
            "importance": self.importance,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
        }


@dataclass
class MemoryChunk:
    chunk_id: str
    memory_id: str
    ordinal: int
    text: str
    tokens: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MemoryEmbedding:
    embedding_id: str
    memory_id: str
    chunk_id: str | None
    dims: int
    vector: list[float]
    model: str = "dummy"

    def to_dict(self) -> dict[str, Any]:
        return {
            "embedding_id": self.embedding_id,
            "memory_id": self.memory_id,
            "chunk_id": self.chunk_id,
            "dims": self.dims,
            "vector": list(self.vector),
            "model": self.model,
        }


@dataclass
class MemoryRelation:
    relation_id: str
    from_id: str
    to_id: str
    relation: str = "related"
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MemorySession:
    session_id: str
    project_id: str | None = None
    agent_id: str | None = None
    status: str = "active"
    working_set: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MemoryHistoryEntry:
    history_id: str
    action: str
    memory_id: str | None = None
    session_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MemoryFeedback:
    feedback_id: str
    memory_id: str
    score: float
    comment: str = ""
    actor: str = "system"
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MemorySearchHit:
    memory_id: str
    score: float
    kind: str
    layer: str
    title: str
    content: str
    snippet: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
