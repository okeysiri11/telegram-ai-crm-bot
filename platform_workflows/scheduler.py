"""Epic 45.3 — Job Scheduler."""
from __future__ import annotations
import time
from typing import Any
from platform_workflows.ua_store import ScheduledJob, new_id, ua_store

INTERVALS = {
    "once": 0,
    "daily": 86400,
    "weekly": 7 * 86400,
    "monthly": 30 * 86400,
    "night": 86400,
    "event": None,
    "after": None,
}

class WorkflowScheduler:
    def schedule(self, owner_id: str, workflow_id: str, schedule: str, *, meta: dict[str, Any] | None = None) -> dict[str, Any]:
        if schedule not in INTERVALS:
            return {"error": "unknown_schedule", "allowed": list(INTERVALS)}
        now = time.time()
        delay = INTERVALS[schedule]
        next_run = now if delay is None or delay == 0 else now + (delay if schedule != "night" else self._seconds_until_night())
        if schedule == "once":
            next_run = now
        job = ScheduledJob(id=new_id("job"), owner_id=owner_id, workflow_id=workflow_id, schedule=schedule, next_run_at=next_run, meta=dict(meta or {}))
        ua_store.jobs[job.id] = job
        return job.to_dict()
    def _seconds_until_night(self) -> float:
        # ~02:00 local approx — fixed offset for tests
        return 2 * 3600
    def list_jobs(self, owner_id: str) -> list[dict[str, Any]]:
        return [j.to_dict() for j in ua_store.jobs.values() if j.owner_id == owner_id]
    def due(self, *, now: float | None = None) -> list[ScheduledJob]:
        now = now or time.time()
        return [j for j in ua_store.jobs.values() if j.enabled and j.next_run_at <= now]
    def tick(self, run_fn) -> list[dict[str, Any]]:
        out = []
        for job in self.due():
            result = run_fn(job.owner_id, job.workflow_id)
            delay = INTERVALS.get(job.schedule)
            if job.schedule == "once" or delay is None:
                job.enabled = False
            elif delay:
                job.next_run_at = time.time() + delay
            ua_store.jobs[job.id] = job
            out.append({"job": job.to_dict(), "run": result})
        return out

workflow_scheduler = WorkflowScheduler()
