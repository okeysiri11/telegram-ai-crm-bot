# Scheduler Engine v1 — scheduled jobs, executions, failures.

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin


class JobScheduleType(str, enum.Enum):
    CRON = "CRON"
    DELAYED = "DELAYED"
    INTERVAL = "INTERVAL"


class ScheduledJobStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    DISABLED = "DISABLED"


class JobExecutionStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    DEAD_LETTER = "DEAD_LETTER"


class ScheduledJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "scheduler_engine_v1_scheduled_jobs"
    __table_args__ = (
        Index("ix_scheduler_engine_v1_jobs_status", "status"),
        Index("ix_scheduler_engine_v1_jobs_next_run", "next_run_at"),
        Index("ix_scheduler_engine_v1_jobs_job_key", "job_key"),
        Index("ix_scheduler_engine_v1_jobs_lock", "lock_owner"),
        UniqueConstraint("job_key", name="uq_scheduler_engine_v1_jobs_job_key"),
    )

    job_key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    schedule_type: Mapped[str] = mapped_column(String(20), nullable=False)
    cron_expression: Mapped[str | None] = mapped_column(String(100), nullable=True)
    interval_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default=ScheduledJobStatus.ACTIVE.value,
        nullable=False,
    )
    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    max_retries: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    lock_owner: Mapped[str | None] = mapped_column(String(64), nullable=True)
    lock_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    owner_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_one_shot: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<ScheduledJob key={self.job_key} status={self.status}>"


class JobExecution(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "scheduler_engine_v1_job_executions"
    __table_args__ = (
        Index("ix_scheduler_engine_v1_exec_job", "job_id"),
        Index("ix_scheduler_engine_v1_exec_status", "status"),
        Index("ix_scheduler_engine_v1_exec_scheduled", "scheduled_at"),
        Index("ix_scheduler_engine_v1_exec_retry", "next_retry_at"),
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scheduler_engine_v1_scheduled_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=JobExecutionStatus.PENDING.value,
        nullable=False,
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    worker_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<JobExecution job={self.job_id} "
            f"status={self.status} attempt={self.attempt_number}>"
        )


class JobFailure(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "scheduler_engine_v1_job_failures"
    __table_args__ = (
        Index("ix_scheduler_engine_v1_fail_exec", "execution_id"),
        Index("ix_scheduler_engine_v1_fail_job", "job_id"),
    )

    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scheduler_engine_v1_job_executions.id", ondelete="CASCADE"),
        nullable=False,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scheduler_engine_v1_scheduled_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    is_terminal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<JobFailure execution={self.execution_id} attempt={self.attempt_number}>"
