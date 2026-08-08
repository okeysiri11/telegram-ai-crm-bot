"""Universal Hercules queue façade (lanes + stats)."""

from __future__ import annotations

from typing import Any

from platform_hercules.core.models import QueueKind
from platform_hercules.scheduler.scheduler import hercules_scheduler


class HerculesQueue:
    """Logical multi-queue over HerculesScheduler (+ optional platform_jobs bridge)."""

    LANE_ALIASES: dict[str, QueueKind] = {
        "task": QueueKind.TASK,
        "ai": QueueKind.AI,
        "image": QueueKind.IMAGE,
        "video": QueueKind.VIDEO,
        "voice": QueueKind.VOICE,
        "workflow": QueueKind.WORKFLOW,
        "notification": QueueKind.NOTIFICATION,
        "telegram": QueueKind.TELEGRAM,
        "publish": QueueKind.PUBLISH,
        "background": QueueKind.BACKGROUND,
        "gpu": QueueKind.GPU,
        "cpu": QueueKind.CPU,
        "realtime": QueueKind.REALTIME,
        "retry": QueueKind.RETRY,
        "delayed": QueueKind.DELAYED,
        "scheduled": QueueKind.SCHEDULED,
    }

    def enqueue(self, job_id: str, lane: str = "task", *, priority: int = 5, delay_sec: float = 0.0) -> None:
        kind = self.LANE_ALIASES.get(lane, QueueKind.TASK)
        hercules_scheduler.enqueue(job_id, queue=kind, priority=priority, delay_sec=delay_sec)

    def snapshot(self) -> dict[str, Any]:
        depths = hercules_scheduler.depths()
        bridge: dict[str, Any] = {}
        try:
            from platform_jobs.unified_queue import QueueLane, unified_queue

            # Sync-safe lane names only (async snapshot exists but not awaited here)
            bridge = {
                "platform_jobs_lanes": [lane.value for lane in QueueLane],
                "bridge": "platform_jobs.unified_queue",
            }
            _ = unified_queue
        except Exception:
            bridge = {}
        return {"hercules_lanes": depths, **bridge}


hercules_queue = HerculesQueue()
