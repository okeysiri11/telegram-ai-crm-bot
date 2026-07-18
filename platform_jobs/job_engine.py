# Job Engine — central facade for all background work.

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from platform_jobs.exceptions import JobCancelledError, JobNotFoundError
from platform_jobs.job_dispatcher import job_dispatcher
from platform_jobs.job_events import JobCancelledEvent
from platform_jobs.job_history import job_history
from platform_jobs.job_metrics import job_metrics
from platform_jobs.job_queue import job_queue
from platform_jobs.job_registry import job_registry
from platform_jobs.job_retry import job_retry
from platform_jobs.job_scheduler import job_scheduler
from platform_jobs.models import JobRecord, JobState, JobType
from platform_jobs.worker_manager import worker_manager

logger = logging.getLogger(__name__)


class JobEngine:
    """All platform background work must go through this engine."""

    async def start(self, *, workers: int = 4) -> None:
        worker_manager.set_max_workers(workers)
        await job_dispatcher.start()
        logger.info("job_engine_started workers=%s", workers)

    async def stop(self, *, graceful: bool = True) -> None:
        await job_dispatcher.stop()
        logger.info("job_engine_stopped")

    def register_handler(self, name: str, handler) -> None:
        job_registry.register(name, handler)

    async def enqueue(
        self,
        handler_name: str,
        payload: dict[str, Any],
        *,
        job_type: JobType = JobType.IMMEDIATE,
        priority: int = 5,
        max_retries: int = 5,
        delay_seconds: float | None = None,
        run_at: datetime | None = None,
        cron_expression: str | None = None,
        interval_seconds: float | None = None,
        pipeline_steps: list[str] | None = None,
        tz: str = "UTC",
    ) -> JobRecord:
        job = JobRecord.new(
            handler_name,
            payload,
            job_type=job_type,
            priority=priority,
            max_retries=max_retries,
            pipeline_steps=pipeline_steps,
        )

        if job_type == JobType.IMMEDIATE:
            return await job_scheduler.submit_immediate(job)
        if job_type == JobType.DELAYED and delay_seconds is not None:
            return await job_scheduler.submit_delayed(job, delay_seconds=delay_seconds)
        if job_type == JobType.SCHEDULED and run_at is not None:
            return await job_scheduler.submit_scheduled(job, run_at=run_at, tz=tz)
        if job_type == JobType.CRON and cron_expression:
            return await job_scheduler.submit_cron(job, cron_expression=cron_expression, tz=tz)
        if job_type == JobType.RECURRING and interval_seconds:
            return await job_scheduler.submit_recurring(job, interval_seconds=interval_seconds)
        if job_type == JobType.PIPELINE:
            return await job_scheduler.submit_pipeline(job)

        return await job_scheduler.submit_immediate(job)

    async def enqueue_batch(self, jobs: list[tuple[str, dict[str, Any]]]) -> list[JobRecord]:
        records = [
            JobRecord.new(name, payload, job_type=JobType.BATCH) for name, payload in jobs
        ]
        return await job_scheduler.submit_batch(records)

    async def cancel(self, job_id: str, *, reason: str = "") -> JobRecord:
        job = await job_queue.get(job_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id} not found")
        job.state = JobState.CANCELLED.value
        await job_queue.update(job)
        from events.event_bus import publish

        await publish(
            JobCancelledEvent(
                job_id=job_id,
                handler_name=job.handler_name,
                reason=reason,
            )
        )
        return job

    async def get_job(self, job_id: str) -> JobRecord:
        job = await job_queue.get(job_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id} not found")
        return job

    async def status(self) -> dict[str, Any]:
        metrics = await job_metrics.snapshot()
        return {
            "handlers": job_registry.list_handlers(),
            "metrics": metrics.to_dict(),
            "workers": worker_manager.health_summary(),
            "scheduler": {
                "scheduled": job_scheduler.list_scheduled(),
                "recurring": job_scheduler.list_recurring(),
            },
            "history": job_history.list(limit=20),
            "retry_history": job_retry.history(limit=20),
            "dead_letter": [j.to_dict() for j in await job_queue.dead_letter_queue()],
        }

    async def dashboard_widgets(self) -> dict[str, Any]:
        metrics = await job_metrics.snapshot()
        workers = worker_manager.health_summary()
        running = await job_queue.list_jobs(state=JobState.RUNNING.value, limit=10)
        failed = await job_queue.list_jobs(state=JobState.FAILED.value, limit=10)
        dead = await job_queue.list_jobs(state=JobState.DEAD_LETTER.value, limit=10)

        return {
            "running_jobs": {"count": metrics.running, "jobs": [j.to_dict() for j in running]},
            "failed_jobs": {
                "count": metrics.failed + metrics.dead_letter,
                "jobs": [j.to_dict() for j in failed + dead],
            },
            "queue_size": {"count": metrics.queued + metrics.retrying},
            "worker_health": workers,
            "execution_rate": {"per_minute": metrics.execution_rate_per_min},
            "retry_rate": {"per_minute": metrics.retry_rate_per_min},
        }

    def reset(self) -> None:
        job_registry.reset()
        job_queue.reset()
        job_retry.reset()
        job_history.reset()
        job_metrics.reset()
        job_scheduler.reset()
        worker_manager.reset()


job_engine = JobEngine()
