"""Project Memory Engine ORM — Sprint 36.5."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class ProjectMemoryRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "project_memory"
    __table_args__ = (
        UniqueConstraint("memory_key", name="uq_project_memory_memory_key"),
        Index("ix_project_memory_kind", "kind"),
        Index("ix_project_memory_layer", "layer"),
        Index("ix_project_memory_project_id", "project_id"),
    )

    memory_key: Mapped[str] = mapped_column(String(64), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False, default="project")
    layer: Mapped[str] = mapped_column(String(32), nullable=False, default="long_term")
    title: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    project_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    agent_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    client_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    workflow_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    document_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tags_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    importance: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class MemoryChunkRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "memory_chunks"
    __table_args__ = (Index("ix_memory_chunks_memory_key", "memory_key"),)

    chunk_key: Mapped[str] = mapped_column(String(64), nullable=False)
    memory_key: Mapped[str] = mapped_column(String(64), nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class MemoryEmbeddingRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "memory_embeddings"
    __table_args__ = (Index("ix_memory_embeddings_memory_key", "memory_key"),)

    embedding_key: Mapped[str] = mapped_column(String(64), nullable=False)
    memory_key: Mapped[str] = mapped_column(String(64), nullable=False)
    chunk_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    dims: Mapped[int] = mapped_column(Integer, nullable=False, default=8)
    vector_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    model: Mapped[str] = mapped_column(String(128), nullable=False, default="dummy")


class MemoryRelationRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "memory_relations"
    __table_args__ = (
        Index("ix_memory_relations_from", "from_key"),
        Index("ix_memory_relations_to", "to_key"),
    )

    relation_key: Mapped[str] = mapped_column(String(64), nullable=False)
    from_key: Mapped[str] = mapped_column(String(64), nullable=False)
    to_key: Mapped[str] = mapped_column(String(64), nullable=False)
    relation: Mapped[str] = mapped_column(String(64), nullable=False, default="related")
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)


class MemorySessionRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "memory_sessions"
    __table_args__ = (
        UniqueConstraint("session_key", name="uq_memory_sessions_session_key"),
        Index("ix_memory_sessions_project_id", "project_id"),
    )

    session_key: Mapped[str] = mapped_column(String(64), nullable=False)
    project_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    agent_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    working_set_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class MemoryHistoryRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "memory_history"
    __table_args__ = (
        Index("ix_memory_history_memory_key", "memory_key"),
        Index("ix_memory_history_session_key", "session_key"),
    )

    history_key: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    memory_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    session_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    details_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class MemoryFeedbackRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "memory_feedback"
    __table_args__ = (Index("ix_memory_feedback_memory_key", "memory_key"),)

    feedback_key: Mapped[str] = mapped_column(String(64), nullable=False)
    memory_key: Mapped[str] = mapped_column(String(64), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    comment: Mapped[str] = mapped_column(Text, nullable=False, default="")
    actor: Mapped[str] = mapped_column(String(128), nullable=False, default="system")
