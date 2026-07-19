# Platform Memory — universal semantic memory entity.

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class MemoryEntity:
    """Universal memory object searchable by meaning."""

    id: str
    owner_id: str | None
    agent_id: str | None
    session_id: str | None
    text: str
    summary: str | None
    embedding: list[float]
    importance_score: float
    created_at: str
    updated_at: str
    expires_at: str | None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "text": self.text,
            "summary": self.summary,
            "embedding": self.embedding,
            "importance_score": self.importance_score,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
            "metadata": self.metadata,
        }

    @classmethod
    def create(
        cls,
        *,
        text: str,
        embedding: list[float],
        owner_id: str | None = None,
        agent_id: str | None = None,
        session_id: str | None = None,
        summary: str | None = None,
        importance_score: float = 0.5,
        expires_at: str | None = None,
        metadata: dict[str, Any] | None = None,
        memory_id: str | None = None,
    ) -> MemoryEntity:
        now = datetime.now(timezone.utc).isoformat()
        return cls(
            id=memory_id or str(uuid4()),
            owner_id=owner_id,
            agent_id=agent_id,
            session_id=session_id,
            text=text,
            summary=summary,
            embedding=list(embedding),
            importance_score=importance_score,
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
            metadata=dict(metadata or {}),
        )


@dataclass(frozen=True)
class MemorySearchHit:
    entity: MemoryEntity
    score: float
    semantic_score: float = 0.0
    keyword_score: float = 0.0
    importance_boost: float = 0.0
    recency_boost: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.entity.to_dict(),
            "score": round(self.score, 4),
            "semantic_score": round(self.semantic_score, 4),
            "keyword_score": round(self.keyword_score, 4),
            "importance_boost": round(self.importance_boost, 4),
            "recency_boost": round(self.recency_boost, 4),
        }


@dataclass(frozen=True)
class MemoryFilters:
    owner_id: str | None = None
    agent_id: str | None = None
    session_id: str | None = None
