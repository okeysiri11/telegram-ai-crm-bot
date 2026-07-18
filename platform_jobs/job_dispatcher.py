# Job dispatcher — routes jobs from queue to workers.

from __future__ import annotations

import asyncio
import logging
import time

from platform_jobs.job_executor import job_executor
from platform_jobs.job_queue import job_queue
from platform_jobs.worker_manager import worker_manager

logger = logging.getLogger(__name__)


class JobDispatcher:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        await worker_manager.start()
        self._task = asyncio.create_task(self._loop(), name="job-dispatcher")
        logger.info("job_dispatcher_started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await worker_manager.shutdown()
        logger.info("job_dispatcher_stopped")

    async def _loop(self) -> None:
        while self._running:
            try:
                await self._tick()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("job_dispatcher_tick_failed")
            await asyncio.sleep(0.05)

    async def _tick(self) -> None:
        if not worker_manager.has_capacity():
            return

        job = await job_queue.dequeue_ready(now=time.monotonic())
        if job is None:
            return

        worker = worker_manager.acquire_worker()
        if worker is None:
            await job_queue.requeue(job)
            return

        asyncio.create_task(self._run_job(job, worker.worker_id))

    async def _run_job(self, job, worker_id: str) -> None:
        try:
            await job_executor.execute(job, worker_id=worker_id)
        except Exception:
            pass
        finally:
            worker_manager.release_worker(worker_id)


job_dispatcher = JobDispatcher()
