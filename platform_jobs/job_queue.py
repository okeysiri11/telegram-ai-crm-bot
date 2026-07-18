# Job queue — priority FIFO with dead letter queue.

from __future__ import annotations

import asyncio
import heapq
import logging
from typing import Any

from platform_jobs.models import JobRecord, JobState

logger = logging.getLogger(__name__)


class _QueueEntry:
    __slots__ = ("priority", "seq", "job_id")

    def __init__(self, priority: int, seq: int, job_id: str) -> None:
        self.priority = priority
        self.seq = seq
        self.job_id = job_id

    def __lt__(self, other: "_QueueEntry") -> bool:
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.seq < other.seq


class JobQueue:
    """Priority queue — lower priority number = higher priority. FIFO within same priority."""

    def __init__(self) -> None:
        self._heap: list[_QueueEntry] = []
        self._seq = 0
        self._jobs: dict[str, JobRecord] = {}
        self._dead_letter: list[JobRecord] = []
        self._lock = asyncio.Lock()

    def reset(self) -> None:
        self._heap.clear()
        self._seq = 0
        self._jobs.clear()
        self._dead_letter.clear()

    async def enqueue(self, job: JobRecord) -> None:
        async with self._lock:
            self._jobs[job.job_id] = job
            heapq.heappush(self._heap, _QueueEntry(job.priority, self._seq, job.job_id))
            self._seq += 1

    async def enqueue_many(self, jobs: list[JobRecord]) -> None:
        async with self._lock:
            for job in jobs:
                self._jobs[job.job_id] = job
                heapq.heappush(self._heap, _QueueEntry(job.priority, self._seq, job.job_id))
                self._seq += 1

    async def dequeue_ready(self, *, now: float | None = None) -> JobRecord | None:
        import time

        current = now if now is not None else time.monotonic()
        async with self._lock:
            while self._heap:
                entry = self._heap[0]
                job = self._jobs.get(entry.job_id)
                if job is None:
                    heapq.heappop(self._heap)
                    continue
                if job.state not in (JobState.PENDING.value, JobState.RETRYING.value):
                    heapq.heappop(self._heap)
                    continue
                if job.run_at is not None and job.run_at > current:
                    return None
                heapq.heappop(self._heap)
                return job
        return None

    async def get(self, job_id: str) -> JobRecord | None:
        async with self._lock:
            return self._jobs.get(job_id)

    async def update(self, job: JobRecord) -> None:
        async with self._lock:
            self._jobs[job.job_id] = job

    async def requeue(self, job: JobRecord) -> None:
        async with self._lock:
            self._jobs[job.job_id] = job
            heapq.heappush(self._heap, _QueueEntry(job.priority, self._seq, job.job_id))
            self._seq += 1

    async def move_to_dead_letter(self, job: JobRecord) -> None:
        job.state = JobState.DEAD_LETTER.value
        async with self._lock:
            self._dead_letter.append(job)
            self._jobs[job.job_id] = job

    async def size(self) -> int:
        async with self._lock:
            return len(self._heap)

    async def count_by_state(self) -> dict[str, int]:
        async with self._lock:
            counts: dict[str, int] = {}
            for job in self._jobs.values():
                counts[job.state] = counts.get(job.state, 0) + 1
            return counts

    async def list_jobs(self, *, state: str | None = None, limit: int = 100) -> list[JobRecord]:
        async with self._lock:
            jobs = list(self._jobs.values())
        if state:
            jobs = [j for j in jobs if j.state == state]
        return jobs[:limit]

    async def dead_letter_queue(self) -> list[JobRecord]:
        async with self._lock:
            return list(self._dead_letter)

    async def total_tracked(self) -> int:
        async with self._lock:
            return len(self._jobs)


job_queue = JobQueue()
