# Job executor — runs registered handlers.

from __future__ import annotations

import inspect
import logging
import time
from datetime import datetime, timezone
from typing import Any

from platform_jobs.exceptions import JobCancelledError, JobHandlerError, JobRetryExhaustedError
from platform_jobs.job_events import JobCompletedEvent, JobFailedEvent, JobStartedEvent
from platform_jobs.job_history import job_history
from platform_jobs.job_metrics import job_metrics
from platform_jobs.job_queue import job_queue
from platform_jobs.job_registry import job_registry
from platform_jobs.job_retry import job_retry
from platform_jobs.job_scheduler import job_scheduler
from platform_jobs.models import JobRecord, JobState

logger = logging.getLogger(__name__)


class JobExecutor:
    async def execute(self, job: JobRecord, *, worker_id: str = "") -> Any:
        if job.state == JobState.CANCELLED.value:
            raise JobCancelledError(f"Job {job.job_id} cancelled")

        job.state = JobState.RUNNING.value
        job.started_at = datetime.now(timezone.utc)
        await job_queue.update(job)

        await self._publish_started(job, worker_id)
        started = time.perf_counter()

        try:
            if job.job_type == "pipeline" and job.pipeline_steps:
                result = await self._execute_pipeline(job)
            else:
                result = await self._execute_handler(job.handler_name, job.payload)

            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            job.state = JobState.COMPLETED.value
            job.completed_at = datetime.now(timezone.utc)
            job.result = result
            await job_queue.update(job)
            job_history.record(job)
            job_metrics.record_completed()
            await self._publish_completed(job, duration_ms)

            if job.job_type in ("cron", "recurring"):
                await job_scheduler.reschedule_recurring(job)

            return result
        except JobCancelledError:
            raise
        except Exception as exc:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            await self._handle_failure(job, str(exc), duration_ms)
            raise

    async def _execute_handler(self, handler_name: str, payload: dict[str, Any]) -> Any:
        handler = job_registry.get(handler_name)
        result = handler(payload)
        if inspect.isawaitable(result):
            return await result
        return result

    async def _execute_pipeline(self, job: JobRecord) -> dict[str, Any]:
        results: dict[str, Any] = {}
        ctx = dict(job.payload)
        for step in job.pipeline_steps:
            step_result = await self._execute_handler(step, ctx)
            results[step] = step_result
            if isinstance(step_result, dict):
                ctx.update(step_result)
        return results

    async def _handle_failure(self, job: JobRecord, error: str, duration_ms: float) -> None:
        await self._publish_failed(job, error)
        try:
            job = job_retry.schedule_retry(job, error)
            job_metrics.record_retry()
            await job_queue.requeue(job)
            await job_retry.publish_retried(job)
        except JobRetryExhaustedError:
            await job_queue.move_to_dead_letter(job)
            job_history.record(job)

    async def _publish_started(self, job: JobRecord, worker_id: str) -> None:
        from events.event_bus import publish

        await publish(
            JobStartedEvent(
                job_id=job.job_id,
                handler_name=job.handler_name,
                worker_id=worker_id,
            )
        )

    async def _publish_completed(self, job: JobRecord, duration_ms: float) -> None:
        from events.event_bus import publish

        await publish(
            JobCompletedEvent(
                job_id=job.job_id,
                handler_name=job.handler_name,
                duration_ms=duration_ms,
            )
        )

    async def _publish_failed(self, job: JobRecord, error: str) -> None:
        from events.event_bus import publish

        await publish(
            JobFailedEvent(
                job_id=job.job_id,
                handler_name=job.handler_name,
                error=error,
                retry_count=job.retry_count,
            )
        )


job_executor = JobExecutor()
