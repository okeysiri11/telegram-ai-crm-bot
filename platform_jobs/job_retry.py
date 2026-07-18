# Job retry — exponential backoff and retry history.

from __future__ import annotations

import logging
import time
from typing import Any

from platform_jobs.exceptions import JobRetryExhaustedError
from platform_jobs.job_events import JobRetriedEvent
from platform_jobs.models import JobRecord, JobState

logger = logging.getLogger(__name__)

BASE_DELAY = 1.0
MAX_DELAY = 300.0


class JobRetryManager:
    def __init__(self) -> None:
        self._history: list[dict[str, Any]] = []

    def reset(self) -> None:
        self._history.clear()

    def compute_delay(self, attempt: int) -> float:
        return min(BASE_DELAY * (2 ** (attempt - 1)), MAX_DELAY)

    def schedule_retry(self, job: JobRecord, error: str) -> JobRecord:
        job.retry_count += 1
        if job.retry_count > job.max_retries:
            job.state = JobState.DEAD_LETTER.value
            job.failure_reason = error
            self._history.append(
                {
                    "job_id": job.job_id,
                    "attempt": job.retry_count,
                    "status": "exhausted",
                    "error": error,
                }
            )
            raise JobRetryExhaustedError(
                f"Job {job.job_id} exhausted {job.max_retries} retries: {error}"
            )

        delay = self.compute_delay(job.retry_count)
        job.state = JobState.RETRYING.value
        job.failure_reason = error
        job.run_at = time.monotonic() + delay

        self._history.append(
            {
                "job_id": job.job_id,
                "attempt": job.retry_count,
                "status": "scheduled",
                "delay_seconds": delay,
                "error": error,
                "next_run_at": job.run_at,
            }
        )
        logger.info(
            "job_retry_scheduled id=%s attempt=%s delay=%.1fs",
            job.job_id,
            job.retry_count,
            delay,
        )
        return job

    async def publish_retried(self, job: JobRecord) -> None:
        from events.event_bus import publish

        await publish(
            JobRetriedEvent(
                job_id=job.job_id,
                handler_name=job.handler_name,
                attempt=job.retry_count,
                next_run_at=job.run_at or 0.0,
            )
        )

    def history(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return self._history[-limit:]


job_retry = JobRetryManager()
