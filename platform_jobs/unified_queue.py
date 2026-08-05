# Unified Queue Architecture — Sprint 32.3.
# Extends platform_jobs.JobQueue — one infra, five logical lanes + retry + DLQ.

from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field
from typing import Any

from platform_jobs.job_queue import JobQueue
from platform_jobs.job_retry import JobRetryManager, job_retry
from platform_jobs.models import JobRecord, JobState, JobType

logger = logging.getLogger(__name__)


class QueueLane(str, enum.Enum):
    AI = "ai"
    WORKFLOW = "workflow"
    BACKGROUND = "background"
    NOTIFICATION = "notification"
    RENDER = "render"


# Lower number = higher priority within the unified heap.
LANE_PRIORITY: dict[QueueLane, int] = {
    QueueLane.NOTIFICATION: 2,
    QueueLane.AI: 3,
    QueueLane.WORKFLOW: 4,
    QueueLane.RENDER: 5,
    QueueLane.BACKGROUND: 6,
}

DEFAULT_MAX_RETRIES: dict[QueueLane, int] = {
    QueueLane.AI: 3,
    QueueLane.WORKFLOW: 5,
    QueueLane.BACKGROUND: 5,
    QueueLane.NOTIFICATION: 4,
    QueueLane.RENDER: 2,
}


@dataclass
class RetryPolicy:
    max_retries: int = 5
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 300.0

    def delay_for(self, attempt: int) -> float:
        return min(self.base_delay_seconds * (2 ** (attempt - 1)), self.max_delay_seconds)


@dataclass
class LaneSnapshot:
    lane: str
    pending: int = 0
    running: int = 0
    retrying: int = 0
    dead_letter: int = 0
    completed: int = 0
    failed: int = 0


@dataclass
class UnifiedQueueSnapshot:
    lanes: dict[str, LaneSnapshot] = field(default_factory=dict)
    dead_letter_total: int = 0
    tracked_total: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "lanes": {k: vars(v) for k, v in self.lanes.items()},
            "dead_letter_total": self.dead_letter_total,
            "tracked_total": self.tracked_total,
        }


class UnifiedQueueArchitecture:
    """
    Logical separation of AI / Workflow / Background / Notification / Render queues
    over a single JobQueue + shared retry / dead-letter policy.
    """

    def __init__(
        self,
        *,
        queue: JobQueue | None = None,
        retry: JobRetryManager | None = None,
    ) -> None:
        self._queue = queue or JobQueue()
        self._retry = retry or job_retry
        self._lane_policies: dict[QueueLane, RetryPolicy] = {
            lane: RetryPolicy(max_retries=DEFAULT_MAX_RETRIES[lane]) for lane in QueueLane
        }

    def reset(self) -> None:
        self._queue.reset()
        self._retry.reset()

    @property
    def queue(self) -> JobQueue:
        return self._queue

    def policy_for(self, lane: QueueLane) -> RetryPolicy:
        return self._lane_policies[lane]

    def lanes(self) -> list[str]:
        return [lane.value for lane in QueueLane]

    async def enqueue(
        self,
        *,
        lane: QueueLane | str,
        handler_name: str,
        payload: dict[str, Any] | None = None,
        priority: int | None = None,
        max_retries: int | None = None,
    ) -> JobRecord:
        lane_e = QueueLane(lane) if isinstance(lane, str) else lane
        policy = self._lane_policies[lane_e]
        body = dict(payload or {})
        body["_queue_lane"] = lane_e.value
        job = JobRecord.new(
            handler_name=handler_name,
            payload=body,
            job_type=JobType.IMMEDIATE,
            priority=priority if priority is not None else LANE_PRIORITY[lane_e],
            max_retries=max_retries if max_retries is not None else policy.max_retries,
        )
        await self._queue.enqueue(job)
        logger.debug("unified_queue_enqueue lane=%s job=%s", lane_e.value, job.job_id)
        return job

    async def dequeue(self, *, lane: QueueLane | str | None = None) -> JobRecord | None:
        job = await self._queue.dequeue_ready()
        if job is None:
            return None
        if lane is not None:
            want = QueueLane(lane).value if isinstance(lane, str) else lane.value
            if job.payload.get("_queue_lane") != want:
                # Not the requested lane — requeue and stop (simple in-memory filter).
                await self._queue.requeue(job)
                return None
        return job

    async def fail_with_retry(self, job: JobRecord, error: str) -> JobRecord | None:
        """Apply retry policy; move to DLQ when exhausted. Returns job or None if dead-lettered."""
        try:
            updated = self._retry.schedule_retry(job, error)
            await self._queue.requeue(updated)
            return updated
        except Exception:
            await self._queue.move_to_dead_letter(job)
            return None

    async def complete(self, job: JobRecord, result: Any = None) -> JobRecord:
        job.state = JobState.COMPLETED.value
        job.result = result
        await self._queue.update(job)
        return job

    async def dead_letter(self) -> list[JobRecord]:
        return await self._queue.dead_letter_queue()

    async def snapshot(self) -> UnifiedQueueSnapshot:
        jobs = await self._queue.list_jobs(limit=10_000)
        dlq = await self._queue.dead_letter_queue()
        lanes: dict[str, LaneSnapshot] = {lane.value: LaneSnapshot(lane=lane.value) for lane in QueueLane}
        for job in jobs:
            lane = str(job.payload.get("_queue_lane") or QueueLane.BACKGROUND.value)
            snap = lanes.setdefault(lane, LaneSnapshot(lane=lane))
            if job.state == JobState.PENDING.value:
                snap.pending += 1
            elif job.state == JobState.RUNNING.value:
                snap.running += 1
            elif job.state == JobState.RETRYING.value:
                snap.retrying += 1
            elif job.state == JobState.DEAD_LETTER.value:
                snap.dead_letter += 1
            elif job.state == JobState.COMPLETED.value:
                snap.completed += 1
            elif job.state == JobState.FAILED.value:
                snap.failed += 1
        return UnifiedQueueSnapshot(
            lanes=lanes,
            dead_letter_total=len(dlq),
            tracked_total=await self._queue.total_tracked(),
        )

    def capabilities(self) -> dict[str, Any]:
        return {
            "lanes": self.lanes(),
            "retry": True,
            "dead_letter": True,
            "system_of_record": "platform_jobs.JobQueue",
            "sprint": "32.3",
        }


unified_queue = UnifiedQueueArchitecture()
