"""Multi-Agent Runtime ORM — Sprint 36.7."""

from __future__ import annotations

from sqlalchemy import Boolean, Float, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class AgentRegistryRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "agent_registry"
    __table_args__ = (
        UniqueConstraint("agent_key", name="uq_agent_registry_agent_key"),
        Index("ix_agent_registry_availability", "availability"),
    )

    agent_key: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    capabilities_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    skills_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    permissions_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    availability: Mapped[str] = mapped_column(String(32), nullable=False, default="available")
    healthy: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class AgentTaskRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "agent_tasks"
    __table_args__ = (
        Index("ix_agent_tasks_status", "status"),
        Index("ix_agent_tasks_session_key", "session_key"),
    )

    task_key: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    capability: Mapped[str] = mapped_column(String(128), nullable=False, default="work")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    agent_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    session_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    plan_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    retries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    timeout_sec: Mapped[float] = mapped_column(Float, nullable=False, default=30.0)
    checkpoint_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    result_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class AgentMessageRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "agent_messages"
    __table_args__ = (
        Index("ix_agent_messages_channel", "channel"),
        Index("ix_agent_messages_topic", "topic"),
    )

    message_key: Mapped[str] = mapped_column(String(64), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False, default="direct")
    source_agent_key: Mapped[str] = mapped_column(String(64), nullable=False)
    target_agent_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    topic: Mapped[str | None] = mapped_column(String(128), nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class AgentSessionRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "agent_sessions"
    __table_args__ = (
        UniqueConstraint("session_key", name="uq_agent_sessions_session_key"),
        Index("ix_agent_sessions_status", "status"),
    )

    session_key: Mapped[str] = mapped_column(String(64), nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False, default="")
    mode: Mapped[str] = mapped_column(String(32), nullable=False, default="sequential")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    agent_ids_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    shared_context_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    shared_memory_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class AgentPlanRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "agent_plans"
    __table_args__ = (
        UniqueConstraint("plan_key", name="uq_agent_plans_plan_key"),
        Index("ix_agent_plans_status", "status"),
    )

    plan_key: Mapped[str] = mapped_column(String(64), nullable=False)
    session_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    goal: Mapped[str] = mapped_column(Text, nullable=False, default="")
    mode: Mapped[str] = mapped_column(String(32), nullable=False, default="sequential")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    steps_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)


class AgentExecutionRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "agent_execution"
    __table_args__ = (
        Index("ix_agent_execution_session_key", "session_key"),
        Index("ix_agent_execution_status", "status"),
    )

    execution_key: Mapped[str] = mapped_column(String(64), nullable=False)
    session_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    plan_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mode: Mapped[str] = mapped_column(String(32), nullable=False, default="sequential")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running")
    results_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    aggregated_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class AgentStatisticsRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "agent_statistics"
    __table_args__ = (Index("ix_agent_statistics_metric_key", "metric_key"),)

    metric_key: Mapped[str] = mapped_column(String(128), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    details_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
