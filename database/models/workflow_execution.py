# workflow_executions ORM — persisted workflow runtime state.

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class WorkflowExecution(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "workflow_executions"
    __table_args__ = (
        Index("ix_workflow_executions_workflow_id", "workflow_id"),
        Index("ix_workflow_executions_vertical", "vertical"),
        Index("ix_workflow_executions_status", "status"),
        Index("ix_workflow_executions_started_at", "started_at"),
    )

    workflow_id: Mapped[str] = mapped_column(String(64), nullable=False)
    vertical: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    current_step: Mapped[str | None] = mapped_column(String(64), nullable=True)
    context_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class WorkflowStepLog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "workflow_step_logs"
    __table_args__ = (
        Index("ix_workflow_step_logs_execution_id", "execution_id"),
        Index("ix_workflow_step_logs_step_id", "step_id"),
    )

    execution_id: Mapped[str] = mapped_column(UUID(as_uuid=True), nullable=False)
    step_id: Mapped[str] = mapped_column(String(64), nullable=False)
    step_type: Mapped[str] = mapped_column(String(32), nullable=False)
    duration_ms: Mapped[float] = mapped_column(nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="OK")
