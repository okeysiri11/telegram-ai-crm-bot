"""Enterprise Event Bus ORM — Sprint 36.1."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class EnterpriseEventStoreRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "event_store"
    __table_args__ = (
        Index("ix_event_store_event_key", "event_key"),
        Index("ix_event_store_topic", "topic"),
        Index("ix_event_store_event_type", "event_type"),
        Index("ix_event_store_tenant", "tenant_id"),
        Index("ix_event_store_occurred_at", "occurred_at"),
    )

    event_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    event_type: Mapped[str] = mapped_column(String(256), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="platform")
    topic: Mapped[str] = mapped_column(String(64), nullable=False, default="platform")
    source_service: Mapped[str] = mapped_column(String(128), nullable=False)
    target_service: Mapped[str | None] = mapped_column(String(128), nullable=True)
    priority: Mapped[str] = mapped_column(String(32), nullable=False, default="normal")
    correlation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    causation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tenant_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    signature: Mapped[str | None] = mapped_column(String(128), nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    metadata_payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    security_context_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    event_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0")
    payload_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class EventTopicRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "event_topics"
    __table_args__ = (UniqueConstraint("name", name="uq_event_topics_name"),)

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    subscriber_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    meta_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class EventSubscriberRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "event_subscribers"
    __table_args__ = (
        Index("ix_event_subscribers_subscriber", "subscriber_id"),
        Index("ix_event_subscribers_topic", "topic"),
    )

    subscription_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    subscriber_id: Mapped[str] = mapped_column(String(128), nullable=False)
    topic: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_type: Mapped[str | None] = mapped_column(String(256), nullable=True)
    event_filter: Mapped[str | None] = mapped_column(String(256), nullable=True)
    priority_min: Mapped[str | None] = mapped_column(String(32), nullable=True)
    tenant_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    regex: Mapped[str | None] = mapped_column(String(256), nullable=True)
    wildcard: Mapped[str | None] = mapped_column(String(256), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    meta_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class EventDeliveryRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "event_delivery"
    __table_args__ = (
        Index("ix_event_delivery_event_key", "event_key"),
        Index("ix_event_delivery_status", "status"),
    )

    delivery_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    event_key: Mapped[str] = mapped_column(String(64), nullable=False)
    subscriber_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)


class DeadLetterQueueRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "dead_letter_queue"
    __table_args__ = (Index("ix_dead_letter_queue_created", "created_at"),)

    dlq_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    event_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    subscriber_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retried: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class EventStatisticsRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "event_statistics"
    __table_args__ = (Index("ix_event_statistics_bucket", "bucket_start"),)

    bucket_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    delivered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    metrics_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class EventReplayRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "event_replay"
    __table_args__ = (Index("ix_event_replay_created", "created_at"),)

    replay_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    actor: Mapped[str] = mapped_column(String(128), nullable=False, default="system")
    filter_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    replayed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    result_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
