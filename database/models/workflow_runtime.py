"""Workflow Runtime ORM — Sprint 36.2."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class WorkflowRegistryRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "workflow_registry"
    __table_args__ = (
        UniqueConstraint("workflow_key", name="uq_workflow_registry_workflow_key"),
        Index("ix_workflow_registry_status", "status"),
    )

    workflow_key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    semver: Mapped[str] = mapped_column(String(64), nullable=False, default="1.0.0")
    owner: Mapped[str] = mapped_column(String(128), nullable=False, default="platform")
    start_step: Mapped[str | None] = mapped_column(String(128), nullable=True)
    definition_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    tags_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WorkflowVersionRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "workflow_versions"
    __table_args__ = (
        UniqueConstraint("workflow_key", "semver", name="uq_workflow_versions_key_semver"),
        Index("ix_workflow_versions_workflow_key", "workflow_key"),
    )

    workflow_key: Mapped[str] = mapped_column(String(128), nullable=False)
    semver: Mapped[str] = mapped_column(String(64), nullable=False)
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    snapshot_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class WorkflowRunRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "workflow_runs"
    __table_args__ = (
        UniqueConstraint("run_key", name="uq_workflow_runs_run_key"),
        Index("ix_workflow_runs_workflow_key", "workflow_key"),
        Index("ix_workflow_runs_status", "status"),
    )

    run_key: Mapped[str] = mapped_column(String(64), nullable=False)
    workflow_key: Mapped[str] = mapped_column(String(128), nullable=False)
    semver: Mapped[str] = mapped_column(String(64), nullable=False, default="1.0.0")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    mode: Mapped[str] = mapped_column(String(32), nullable=False, default="sync")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    context_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    timeout_sec: Mapped[float] = mapped_column(Float, nullable=False, default=120.0)
    rollback_of: Mapped[str | None] = mapped_column(String(64), nullable=True)


class WorkflowStepRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "workflow_steps"
    __table_args__ = (Index("ix_workflow_steps_run_key", "run_key"),)

    run_key: Mapped[str] = mapped_column(String(64), nullable=False)
    step_key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False, default="task")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WorkflowVariableRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "workflow_variables"
    __table_args__ = (
        UniqueConstraint("run_key", "name", name="uq_workflow_variables_run_name"),
        Index("ix_workflow_variables_run_key", "run_key"),
    )

    run_key: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    value_json: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSONB, nullable=True)


class WorkflowLogRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "workflow_logs"
    __table_args__ = (Index("ix_workflow_logs_run_key", "run_key"),)

    run_key: Mapped[str] = mapped_column(String(64), nullable=False)
    event: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    logged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class WorkflowCheckpointRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "workflow_checkpoints"
    __table_args__ = (Index("ix_workflow_checkpoints_run_key", "run_key"),)

    run_key: Mapped[str] = mapped_column(String(64), nullable=False)
    checkpoint_key: Mapped[str] = mapped_column(String(64), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    vars_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
