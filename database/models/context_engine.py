"""Context Engine ORM — Sprint 36.4."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class ContextSessionRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "context_sessions"
    __table_args__ = (
        UniqueConstraint("session_key", name="uq_context_sessions_session_key"),
        Index("ix_context_sessions_status", "status"),
    )

    session_key: Mapped[str] = mapped_column(String(64), nullable=False)
    user_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tenant_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    workspace_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    principal: Mapped[str] = mapped_column(String(128), nullable=False, default="system")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    fragment_ids_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_payload: Mapped[dict] = mapped_column("payload_json", JSONB, nullable=False, default=dict)


class ContextSourceRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "context_sources"
    __table_args__ = (
        UniqueConstraint("source_key", name="uq_context_sources_source_key"),
        Index("ix_context_sources_enabled", "enabled"),
    )

    source_key: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(256), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    config_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class ContextCacheRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "context_cache"
    __table_args__ = (
        UniqueConstraint("cache_key", name="uq_context_cache_cache_key"),
        Index("ix_context_cache_expires_at", "expires_at"),
    )

    cache_key: Mapped[str] = mapped_column(String(128), nullable=False)
    bundle_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    hits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ContextHistoryRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "context_history"
    __table_args__ = (Index("ix_context_history_session_key", "session_key"),)

    history_key: Mapped[str] = mapped_column(String(64), nullable=False)
    session_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    details_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class ContextPermissionRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "context_permissions"
    __table_args__ = (
        Index("ix_context_permissions_principal", "principal"),
        Index("ix_context_permissions_source", "source_key"),
    )

    permission_key: Mapped[str] = mapped_column(String(64), nullable=False)
    principal: Mapped[str] = mapped_column(String(128), nullable=False)
    source_key: Mapped[str] = mapped_column(String(64), nullable=False, default="*")
    action: Mapped[str] = mapped_column(String(32), nullable=False, default="read")
    max_sensitivity: Mapped[str] = mapped_column(String(32), nullable=False, default="internal")
    isolation_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    policy_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class ContextEmbeddingRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "context_embeddings"
    __table_args__ = (Index("ix_context_embeddings_fragment_key", "fragment_key"),)

    embedding_key: Mapped[str] = mapped_column(String(64), nullable=False)
    fragment_key: Mapped[str] = mapped_column(String(64), nullable=False)
    dims: Mapped[int] = mapped_column(Integer, nullable=False, default=8)
    vector_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    model: Mapped[str] = mapped_column(String(128), nullable=False, default="dummy")


class ContextStatisticsRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "context_statistics"
    __table_args__ = (Index("ix_context_statistics_metric_key", "metric_key"),)

    metric_key: Mapped[str] = mapped_column(String(128), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    details_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
