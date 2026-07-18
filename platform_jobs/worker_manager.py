# Worker manager — dynamic pool, concurrency, graceful shutdown.

from __future__ import annotations

import asyncio
import logging
import time
import uuid

from platform_jobs.exceptions import WorkerError
from platform_jobs.models import WorkerInfo

logger = logging.getLogger(__name__)


class WorkerManager:
    def __init__(self, *, max_workers: int = 8) -> None:
        self._max_workers = max_workers
        self._workers: dict[str, WorkerInfo] = {}
        self._active_count = 0
        self._lock = asyncio.Lock()
        self._shutting_down = False

    def reset(self) -> None:
        self._workers.clear()
        self._active_count = 0
        self._shutting_down = False

    async def start(self, *, count: int | None = None) -> None:
        n = count or self._max_workers
        async with self._lock:
            for _ in range(n):
                wid = str(uuid.uuid4())
                self._workers[wid] = WorkerInfo(worker_id=wid, status="idle")
        logger.info("job_workers_started count=%s", n)

    async def shutdown(self, *, graceful: bool = True) -> None:
        self._shutting_down = True
        if graceful:
            for _ in range(50):
                async with self._lock:
                    if self._active_count == 0:
                        break
                await asyncio.sleep(0.1)
        async with self._lock:
            self._workers.clear()
        logger.info("job_workers_shutdown graceful=%s", graceful)

    def set_max_workers(self, count: int) -> None:
        self._max_workers = max(count, 1)

    def has_capacity(self) -> bool:
        if self._shutting_down:
            return False
        idle = sum(1 for w in self._workers.values() if w.status == "idle" and w.healthy)
        return idle > 0

    def acquire_worker(self) -> WorkerInfo | None:
        for worker in self._workers.values():
            if worker.status == "idle" and worker.healthy:
                worker.status = "busy"
                self._active_count += 1
                worker.last_heartbeat = time.monotonic()
                return worker
        return None

    def release_worker(self, worker_id: str) -> None:
        worker = self._workers.get(worker_id)
        if worker is None:
            return
        worker.status = "idle"
        worker.current_job_id = None
        worker.jobs_processed += 1
        worker.last_heartbeat = time.monotonic()
        self._active_count = max(self._active_count - 1, 0)

    def heartbeat(self) -> None:
        now = time.monotonic()
        for worker in self._workers.values():
            worker.last_heartbeat = now
            worker.healthy = (now - worker.last_heartbeat) < 120 or worker.status == "busy"

    def list_workers(self) -> list[WorkerInfo]:
        return list(self._workers.values())

    def health_summary(self) -> dict:
        workers = self.list_workers()
        healthy = sum(1 for w in workers if w.healthy)
        return {
            "total": len(workers),
            "healthy": healthy,
            "busy": sum(1 for w in workers if w.status == "busy"),
            "idle": sum(1 for w in workers if w.status == "idle"),
            "max_concurrency": self._max_workers,
            "shutting_down": self._shutting_down,
        }


worker_manager = WorkerManager()
