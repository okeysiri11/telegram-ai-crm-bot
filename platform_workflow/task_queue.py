# Task queue — priority FIFO with retry, delay, and scheduling.

from __future__ import annotations

import asyncio
import heapq
import logging
import time

from platform_workflow.models import Task, TaskPriority, TaskStatus

logger = logging.getLogger(__name__)


class _QueueEntry:
    __slots__ = ("priority", "seq", "task_id")

    def __init__(self, priority: int, seq: int, task_id: str) -> None:
        self.priority = priority
        self.seq = seq
        self.task_id = task_id

    def __lt__(self, other: "_QueueEntry") -> bool:
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.seq < other.seq


class TaskQueue:
    """Priority queue — lower priority value = higher priority. FIFO within same priority."""

    def __init__(self) -> None:
        self._heap: list[_QueueEntry] = []
        self._seq = 0
        self._tasks: dict[str, Task] = {}
        self._lock = asyncio.Lock()

    def reset(self) -> None:
        self._heap.clear()
        self._seq = 0
        self._tasks.clear()

    async def enqueue(self, task: Task, *, run_at: float | None = None) -> None:
        task.status = TaskStatus.QUEUED
        task.run_at = run_at
        task.updated_at = time.time()
        async with self._lock:
            self._tasks[task.task_id] = task
            priority = int(task.priority.value if isinstance(task.priority, TaskPriority) else task.priority)
            heapq.heappush(self._heap, _QueueEntry(priority, self._seq, task.task_id))
            self._seq += 1

    async def enqueue_delayed(self, task: Task, delay_seconds: float) -> None:
        await self.enqueue(task, run_at=time.monotonic() + delay_seconds)

    async def enqueue_scheduled(self, task: Task, scheduled_at: float) -> None:
        task.scheduled_at = scheduled_at
        await self.enqueue(task, run_at=scheduled_at)

    async def dequeue_ready(self, *, now: float | None = None) -> Task | None:
        current = now if now is not None else time.monotonic()
        async with self._lock:
            while self._heap:
                entry = self._heap[0]
                task = self._tasks.get(entry.task_id)
                if task is None:
                    heapq.heappop(self._heap)
                    continue
                if task.status not in (TaskStatus.QUEUED, TaskStatus.ASSIGNED):
                    heapq.heappop(self._heap)
                    continue
                if task.run_at is not None and task.run_at > current:
                    return None
                heapq.heappop(self._heap)
                return task
        return None

    async def requeue_for_retry(self, task: Task, delay_seconds: float) -> None:
        task.retry_count += 1
        task.status = TaskStatus.QUEUED
        task.updated_at = time.time()
        await self.enqueue(task, run_at=time.monotonic() + delay_seconds)

    async def get(self, task_id: str) -> Task | None:
        async with self._lock:
            return self._tasks.get(task_id)

    async def update(self, task: Task) -> None:
        async with self._lock:
            self._tasks[task.task_id] = task

    def length(self) -> int:
        return len(self._heap)

    def all_tasks(self) -> list[Task]:
        return list(self._tasks.values())


task_queue = TaskQueue()
