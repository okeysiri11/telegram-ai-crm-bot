# Job metrics — execution and retry rates.

from __future__ import annotations

import time

from platform_jobs.job_queue import job_queue
from platform_jobs.models import JobMetricsSnapshot, JobState


class JobMetrics:
    def __init__(self) -> None:
        self._completed_window: list[float] = []
        self._retry_window: list[float] = []
        self._window_start = time.monotonic()

    def reset(self) -> None:
        self._completed_window.clear()
        self._retry_window.clear()
        self._window_start = time.monotonic()

    def record_completed(self) -> None:
        self._completed_window.append(time.monotonic())

    def record_retry(self) -> None:
        self._retry_window.append(time.monotonic())

    def _rate_per_minute(self, timestamps: list[float]) -> float:
        now = time.monotonic()
        cutoff = now - 60.0
        recent = [ts for ts in timestamps if ts > cutoff]
        return round(len(recent), 2)

    async def snapshot(self) -> JobMetricsSnapshot:
        counts = await job_queue.count_by_state()
        queued = await job_queue.size()
        return JobMetricsSnapshot(
            queued=queued,
            running=counts.get(JobState.RUNNING.value, 0),
            completed=counts.get(JobState.COMPLETED.value, 0),
            failed=counts.get(JobState.FAILED.value, 0),
            retrying=counts.get(JobState.RETRYING.value, 0),
            dead_letter=counts.get(JobState.DEAD_LETTER.value, 0),
            cancelled=counts.get(JobState.CANCELLED.value, 0),
            execution_rate_per_min=self._rate_per_minute(self._completed_window),
            retry_rate_per_min=self._rate_per_minute(self._retry_window),
        )


job_metrics = JobMetrics()
