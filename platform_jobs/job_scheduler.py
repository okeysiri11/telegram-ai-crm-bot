# Job scheduler — cron, interval, one-time, delayed execution.

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

from platform_jobs.cron_manager import cron_manager
from platform_jobs.exceptions import SchedulerError
from platform_jobs.job_events import JobCreatedEvent
from platform_jobs.job_queue import job_queue
from platform_jobs.models import JobRecord, JobType

logger = logging.getLogger(__name__)


class JobScheduler:
    def __init__(self) -> None:
        self._scheduled: dict[str, JobRecord] = {}
        self._recurring: dict[str, JobRecord] = {}

    def reset(self) -> None:
        self._scheduled.clear()
        self._recurring.clear()

    async def submit_immediate(self, job: JobRecord) -> JobRecord:
        job.run_at = time.monotonic()
        await job_queue.enqueue(job)
        await self._publish_created(job)
        return job

    async def submit_delayed(self, job: JobRecord, *, delay_seconds: float) -> JobRecord:
        job.job_type = JobType.DELAYED.value
        job.run_at = time.monotonic() + delay_seconds
        await job_queue.enqueue(job)
        await self._publish_created(job)
        return job

    async def submit_scheduled(
        self,
        job: JobRecord,
        *,
        run_at: datetime,
        tz: str = "UTC",
    ) -> JobRecord:
        job.job_type = JobType.SCHEDULED.value
        job.timezone = tz
        if run_at.tzinfo is None:
            run_at = run_at.replace(tzinfo=timezone.utc)
        job.run_at = run_at.timestamp()
        self._scheduled[job.job_id] = job
        await job_queue.enqueue(job)
        await self._publish_created(job)
        return job

    async def submit_cron(
        self,
        job: JobRecord,
        *,
        cron_expression: str,
        tz: str = "UTC",
    ) -> JobRecord:
        if not cron_manager.validate(cron_expression):
            raise SchedulerError(f"Invalid cron expression: {cron_expression}")

        job.job_type = JobType.CRON.value
        job.cron_expression = cron_expression
        job.timezone = tz
        job.run_at = cron_manager.next_run(cron_expression, tz=tz)
        self._recurring[job.job_id] = job
        await job_queue.enqueue(job)
        await self._publish_created(job)
        return job

    async def submit_recurring(
        self,
        job: JobRecord,
        *,
        interval_seconds: float,
    ) -> JobRecord:
        job.job_type = JobType.RECURRING.value
        job.interval_seconds = interval_seconds
        job.run_at = time.monotonic() + interval_seconds
        self._recurring[job.job_id] = job
        await job_queue.enqueue(job)
        await self._publish_created(job)
        return job

    async def submit_batch(self, jobs: list[JobRecord]) -> list[JobRecord]:
        now = time.monotonic()
        for job in jobs:
            job.job_type = JobType.BATCH.value
            job.run_at = now
        await job_queue.enqueue_many(jobs)
        for job in jobs:
            await self._publish_created(job)
        return jobs

    async def submit_pipeline(self, job: JobRecord) -> JobRecord:
        job.job_type = JobType.PIPELINE.value
        job.run_at = time.monotonic()
        await job_queue.enqueue(job)
        await self._publish_created(job)
        return job

    async def reschedule_recurring(self, job: JobRecord) -> None:
        from platform_jobs.models import JobState

        if job.job_type == JobType.CRON.value and job.cron_expression:
            job.run_at = cron_manager.next_run(job.cron_expression, tz=job.timezone)
            job.state = JobState.PENDING.value
            await job_queue.requeue(job)
        elif job.job_type == JobType.RECURRING.value and job.interval_seconds:
            import time

            job.run_at = time.monotonic() + job.interval_seconds
            job.state = JobState.PENDING.value
            await job_queue.requeue(job)

    def list_scheduled(self) -> list[dict[str, Any]]:
        return [j.to_dict() for j in self._scheduled.values()]

    def list_recurring(self) -> list[dict[str, Any]]:
        return [j.to_dict() for j in self._recurring.values()]

    @staticmethod
    async def _publish_created(job: JobRecord) -> None:
        from events.event_bus import publish

        await publish(
            JobCreatedEvent(
                job_id=job.job_id,
                job_type=job.job_type,
                handler_name=job.handler_name,
            )
        )


job_scheduler = JobScheduler()
