# Scheduler Engine v1 repositories.

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.scheduler_engine import (
    JobExecution,
    JobExecutionStatus,
    JobFailure,
    JobScheduleType,
    ScheduledJob,
    ScheduledJobStatus,
)


class ScheduledJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        job_key: str,
        name: str,
        schedule_type: str,
        cron_expression: str | None = None,
        interval_seconds: int | None = None,
        run_at: datetime | None = None,
        config: dict | None = None,
        status: str = ScheduledJobStatus.ACTIVE.value,
        next_run_at: datetime | None = None,
        max_retries: int = 5,
        owner_user_id: int | None = None,
        description: str | None = None,
        is_one_shot: bool = False,
        **extra: Any,
    ) -> ScheduledJob:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if schedule_type not in {t.value for t in JobScheduleType}:
            raise ValueError(f"Invalid schedule_type: {schedule_type}")
        if status not in {s.value for s in ScheduledJobStatus}:
            raise ValueError(f"Invalid status: {status}")

        job = ScheduledJob(
            job_key=job_key,
            name=name,
            schedule_type=schedule_type,
            cron_expression=cron_expression,
            interval_seconds=interval_seconds,
            run_at=run_at,
            config=config,
            status=status,
            next_run_at=next_run_at,
            max_retries=max_retries,
            owner_user_id=owner_user_id,
            description=description,
            is_one_shot=is_one_shot,
        )
        self._session.add(job)
        await self._session.flush()
        return job

    async def get_by_id(self, job_id: uuid.UUID) -> ScheduledJob | None:
        result = await self._session.execute(
            select(ScheduledJob).where(ScheduledJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_by_key(self, job_key: str) -> ScheduledJob | None:
        result = await self._session.execute(
            select(ScheduledJob).where(ScheduledJob.job_key == job_key)
        )
        return result.scalar_one_or_none()

    async def list_active(self) -> list[ScheduledJob]:
        result = await self._session.execute(
            select(ScheduledJob)
            .where(ScheduledJob.status == ScheduledJobStatus.ACTIVE.value)
            .order_by(ScheduledJob.next_run_at.asc().nulls_last())
        )
        return list(result.scalars().all())

    async def claim_due(
        self,
        *,
        now: datetime,
        worker_id: str,
        lock_ttl_seconds: int,
        limit: int = 10,
    ) -> list[ScheduledJob]:
        lock_expires = now + timedelta(seconds=lock_ttl_seconds)
        result = await self._session.execute(
            select(ScheduledJob)
            .where(
                ScheduledJob.status == ScheduledJobStatus.ACTIVE.value,
                ScheduledJob.next_run_at.is_not(None),
                ScheduledJob.next_run_at <= now,
                or_(
                    ScheduledJob.lock_owner.is_(None),
                    ScheduledJob.lock_expires_at.is_(None),
                    ScheduledJob.lock_expires_at < now,
                ),
            )
            .order_by(ScheduledJob.next_run_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        jobs = list(result.scalars().all())
        for job in jobs:
            job.lock_owner = worker_id
            job.lock_expires_at = lock_expires
        if jobs:
            await self._session.flush()
        return jobs

    async def release_lock(self, job_id: uuid.UUID) -> None:
        job = await self.get_by_id(job_id)
        if job is None:
            return
        job.lock_owner = None
        job.lock_expires_at = None
        await self._session.flush()

    async def update_schedule(
        self,
        job: ScheduledJob,
        *,
        next_run_at: datetime | None,
        last_run_at: datetime | None = None,
        status: str | None = None,
    ) -> None:
        job.next_run_at = next_run_at
        if last_run_at is not None:
            job.last_run_at = last_run_at
        if status is not None:
            job.status = status
        await self._session.flush()


class JobExecutionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        job_id: uuid.UUID,
        scheduled_at: datetime,
        attempt_number: int = 1,
        status: str = JobExecutionStatus.PENDING.value,
        worker_id: str | None = None,
        **extra: Any,
    ) -> JobExecution:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        execution = JobExecution(
            job_id=job_id,
            scheduled_at=scheduled_at,
            attempt_number=attempt_number,
            status=status,
            worker_id=worker_id,
        )
        self._session.add(execution)
        await self._session.flush()
        return execution

    async def get_by_id(self, execution_id: uuid.UUID) -> JobExecution | None:
        result = await self._session.execute(
            select(JobExecution).where(JobExecution.id == execution_id)
        )
        return result.scalar_one_or_none()

    async def claim_retries(
        self,
        *,
        now: datetime,
        limit: int = 10,
    ) -> list[JobExecution]:
        result = await self._session.execute(
            select(JobExecution)
            .where(
                JobExecution.status == JobExecutionStatus.FAILED.value,
                JobExecution.next_retry_at.is_not(None),
                JobExecution.next_retry_at <= now,
            )
            .order_by(JobExecution.next_retry_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        return list(result.scalars().all())

    async def mark_running(
        self,
        execution: JobExecution,
        *,
        worker_id: str,
        started_at: datetime,
    ) -> None:
        execution.status = JobExecutionStatus.RUNNING.value
        execution.worker_id = worker_id
        execution.started_at = started_at

    async def mark_completed(
        self,
        execution: JobExecution,
        *,
        completed_at: datetime,
        result: dict | None = None,
    ) -> None:
        execution.status = JobExecutionStatus.COMPLETED.value
        execution.completed_at = completed_at
        execution.result = result
        execution.error_message = None
        execution.next_retry_at = None

    async def mark_failed(
        self,
        execution: JobExecution,
        *,
        error_message: str,
        next_retry_at: datetime | None = None,
        terminal: bool = False,
    ) -> None:
        execution.status = (
            JobExecutionStatus.DEAD_LETTER.value
            if terminal
            else JobExecutionStatus.FAILED.value
        )
        execution.error_message = error_message
        execution.next_retry_at = next_retry_at
        execution.completed_at = datetime.now(timezone.utc)


class JobFailureRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        execution_id: uuid.UUID,
        job_id: uuid.UUID,
        attempt_number: int,
        error_message: str,
        is_terminal: bool = False,
        **extra: Any,
    ) -> JobFailure:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        failure = JobFailure(
            execution_id=execution_id,
            job_id=job_id,
            attempt_number=attempt_number,
            error_message=error_message,
            is_terminal=is_terminal,
        )
        self._session.add(failure)
        await self._session.flush()
        return failure

    async def list_for_execution(self, execution_id: uuid.UUID) -> list[JobFailure]:
        result = await self._session.execute(
            select(JobFailure)
            .where(JobFailure.execution_id == execution_id)
            .order_by(JobFailure.attempt_number.asc())
        )
        return list(result.scalars().all())
