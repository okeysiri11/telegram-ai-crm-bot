# AI Memory & Knowledge domain models.

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class MemoryType(str, Enum):
    CONVERSATION = "conversation"
    WORKFLOW = "workflow"
    USER = "user"
    MANAGER = "manager"
    PLUGIN = "plugin"
    ORGANIZATION = "organization"
    SESSION = "session"
    TEMPORARY = "temporary"
    LONG_TERM = "long_term"


class KnowledgeType(str, Enum):
    MARKDOWN = "markdown"
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"
    JSON = "json"
    YAML = "yaml"
    CSV = "csv"


class SearchMode(str, Enum):
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


class ChunkStrategy(str, Enum):
    FIXED_SIZE = "fixed_size"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    SLIDING_WINDOW = "sliding_window"


@dataclass
class MemoryRecord:
    memory_id: str
    memory_type: str
    content: str
    key: str = ""
    plugin_id: str | None = None
    user_id: str | None = None
    workflow_id: str | None = None
    session_id: str | None = None
    organization_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "memory_type": self.memory_type,
            "key": self.key,
            "content": self.content,
            "plugin_id": self.plugin_id,
            "user_id": self.user_id,
            "workflow_id": self.workflow_id,
            "session_id": self.session_id,
            "organization_id": self.organization_id,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
        }


@dataclass
class KnowledgeDocument:
    document_id: str
    title: str
    content: str
    doc_type: str = KnowledgeType.TXT.value
    plugin_id: str | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    chunk_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "title": self.title,
            "doc_type": self.doc_type,
            "plugin_id": self.plugin_id,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "chunk_count": self.chunk_count,
            "content_length": len(self.content),
        }


@dataclass
class DocumentChunk:
    chunk_id: str
    document_id: str
    content: str
    index: int = 0
    embedding: list[float] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "content": self.content,
            "index": self.index,
            "metadata": self.metadata,
        }


@dataclass
class SearchResult:
    result_id: str
    source_type: str  # memory | knowledge
    content: str
    score: float = 0.0
    memory_id: str | None = None
    document_id: str | None = None
    chunk_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_id": self.result_id,
            "source_type": self.source_type,
            "content": self.content,
            "score": round(self.score, 4),
            "memory_id": self.memory_id,
            "document_id": self.document_id,
            "chunk_id": self.chunk_id,
            "metadata": self.metadata,
        }


@dataclass
class RememberRequest:
    content: str
    memory_type: str = MemoryType.CONVERSATION.value
    key: str = ""
    plugin_id: str | None = None
    user_id: str | None = None
    workflow_id: str | None = None
    session_id: str | None = None
    organization_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    memory_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class IndexRequest:
    title: str
    content: str
    doc_type: str = KnowledgeType.TXT.value
    document_id: str = field(default_factory=lambda: str(uuid4()))
    plugin_id: str | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    chunk_strategy: str = ChunkStrategy.PARAGRAPH.value


@dataclass
class AIContextBundle:
    """Injected into every AI Skill and Workflow execution."""

    relevant_memory: list[dict[str, Any]] = field(default_factory=list)
    relevant_knowledge: list[dict[str, Any]] = field(default_factory=list)
    conversation_history: list[dict[str, Any]] = field(default_factory=list)
    plugin_context: dict[str, Any] = field(default_factory=dict)
    configuration: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "relevant_memory": self.relevant_memory,
            "relevant_knowledge": self.relevant_knowledge,
            "conversation_history": self.conversation_history,
            "plugin_context": self.plugin_context,
            "configuration": self.configuration,
        }
