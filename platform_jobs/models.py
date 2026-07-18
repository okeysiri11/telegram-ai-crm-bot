# Job Engine domain models.

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable


class JobType(str, enum.Enum):
    IMMEDIATE = "immediate"
    DELAYED = "delayed"
    SCHEDULED = "scheduled"
    RECURRING = "recurring"
    CRON = "cron"
    BATCH = "batch"
    PIPELINE = "pipeline"


class JobState(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    DEAD_LETTER = "dead_letter"


JobHandler = Callable[[dict[str, Any]], Awaitable[Any] | Any]


@dataclass
class JobRecord:
    job_id: str
    job_type: str
    handler_name: str
    payload: dict[str, Any]
    state: str = JobState.PENDING.value
    priority: int = 5
    max_retries: int = 5
    retry_count: int = 0
    failure_reason: str | None = None
    scheduled_at: float | None = None
    run_at: float | None = None
    cron_expression: str | None = None
    interval_seconds: float | None = None
    timezone: str = "UTC"
    pipeline_steps: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: Any = None

    @staticmethod
    def new(
        handler_name: str,
        payload: dict[str, Any],
        *,
        job_type: JobType = JobType.IMMEDIATE,
        priority: int = 5,
        max_retries: int = 5,
        scheduled_at: float | None = None,
        cron_expression: str | None = None,
        interval_seconds: float | None = None,
        pipeline_steps: list[str] | None = None,
    ) -> JobRecord:
        return JobRecord(
            job_id=str(uuid.uuid4()),
            job_type=job_type.value,
            handler_name=handler_name,
            payload=payload,
            priority=priority,
            max_retries=max_retries,
            scheduled_at=scheduled_at,
            cron_expression=cron_expression,
            interval_seconds=interval_seconds,
            pipeline_steps=pipeline_steps or [],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "handler_name": self.handler_name,
            "payload": self.payload,
            "state": self.state,
            "priority": self.priority,
            "max_retries": self.max_retries,
            "retry_count": self.retry_count,
            "failure_reason": self.failure_reason,
            "scheduled_at": self.scheduled_at,
            "run_at": self.run_at,
            "cron_expression": self.cron_expression,
            "interval_seconds": self.interval_seconds,
            "timezone": self.timezone,
            "pipeline_steps": self.pipeline_steps,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class WorkerInfo:
    worker_id: str
    status: str = "idle"
    current_job_id: str | None = None
    jobs_processed: int = 0
    last_heartbeat: float = field(default_factory=time.monotonic)
    healthy: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "status": self.status,
            "current_job_id": self.current_job_id,
            "jobs_processed": self.jobs_processed,
            "last_heartbeat": self.last_heartbeat,
            "healthy": self.healthy,
        }


@dataclass
class JobMetricsSnapshot:
    queued: int = 0
    running: int = 0
    completed: int = 0
    failed: int = 0
    retrying: int = 0
    dead_letter: int = 0
    cancelled: int = 0
    execution_rate_per_min: float = 0.0
    retry_rate_per_min: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "queued": self.queued,
            "running": self.running,
            "completed": self.completed,
            "failed": self.failed,
            "retrying": self.retrying,
            "dead_letter": self.dead_letter,
            "cancelled": self.cancelled,
            "execution_rate_per_min": self.execution_rate_per_min,
            "retry_rate_per_min": self.retry_rate_per_min,
        }
