"""AI Kernel — system/task/resource/agent/memory/workflow schedulers (Sprint 12.4)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.ai_os.config import DEFAULT_CONFIG
from applications.ai_os.shared.exceptions import NotFoundError, ValidationError
from applications.ai_os.shared.store import AIOSStore, ai_os_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AIKernel:
    def __init__(self, store: AIOSStore | None = None) -> None:
        self.store = store or ai_os_store
        self.schedulers = list(DEFAULT_CONFIG.schedulers)
        self._booted = False

    def boot(self) -> dict[str, Any]:
        self._booted = True
        for name in self.schedulers:
            sid = f"sched_{name}"
            if self.store.schedules.get(sid) is None:
                self.store.schedules.save(
                    sid,
                    {
                        "scheduler_id": sid,
                        "name": name,
                        "status": "running",
                        "queued": 0,
                        "completed": 0,
                        "booted_at": _now(),
                    },
                )
        return {"kernel": "booted", "schedulers": self.schedulers, "at": _now()}

    def schedule(
        self,
        *,
        scheduler: str,
        payload: dict[str, Any] | None = None,
        priority: int = 5,
        name: str = "",
    ) -> dict[str, Any]:
        if not self._booted:
            self.boot()
        if scheduler not in self.schedulers:
            raise ValidationError(f"scheduler must be one of {self.schedulers}")
        sid = f"sched_{scheduler}"
        sched = self.store.schedules.get(sid)
        if sched is None:
            raise NotFoundError("scheduler", sid)
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        job = {
            "job_id": job_id,
            "scheduler": scheduler,
            "name": name or f"{scheduler}_job",
            "priority": max(1, min(10, int(priority))),
            "payload": dict(payload or {}),
            "status": "queued",
            "created_at": _now(),
        }
        self.store.schedules.save(job_id, job)
        sched["queued"] = int(sched.get("queued", 0)) + 1
        self.store.schedules.save(sid, sched)
        return job

    def tick(self, scheduler: str) -> dict[str, Any]:
        if scheduler not in self.schedulers:
            raise ValidationError(f"scheduler must be one of {self.schedulers}")
        queued = [
            j
            for j in self.store.schedules.list_all()
            if j.get("scheduler") == scheduler and j.get("status") == "queued" and j.get("job_id")
        ]
        queued.sort(key=lambda j: (-int(j.get("priority", 5)), j.get("created_at", "")))
        if not queued:
            return {"scheduler": scheduler, "processed": 0}
        job = queued[0]
        job["status"] = "completed"
        job["completed_at"] = _now()
        self.store.schedules.save(job["job_id"], job)
        sid = f"sched_{scheduler}"
        sched = self.store.schedules.get(sid) or {}
        sched["queued"] = max(0, int(sched.get("queued", 1)) - 1)
        sched["completed"] = int(sched.get("completed", 0)) + 1
        self.store.schedules.save(sid, sched)
        return {"scheduler": scheduler, "processed": 1, "job": job}

    def list_schedulers(self) -> list[dict[str, Any]]:
        if not self._booted:
            self.boot()
        return [self.store.schedules.get(f"sched_{n}") for n in self.schedulers if self.store.schedules.get(f"sched_{n}")]

    def status(self) -> dict[str, Any]:
        return {
            "ai_kernel": "1.0",
            "booted": self._booted,
            "schedulers": self.schedulers,
            "ready": True,
        }


ai_kernel = AIKernel()
