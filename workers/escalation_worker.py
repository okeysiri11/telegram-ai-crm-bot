# Escalation worker — polls SLA breaches every 30 seconds.

from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_INTERVAL_SEC = 30


class EscalationWorker:
    def __init__(self, *, interval_sec: int = DEFAULT_INTERVAL_SEC) -> None:
        self.interval_sec = interval_sec
        self._task: asyncio.Task | None = None
        self._running = False
        self._tick_lock = asyncio.Lock()

    @property
    def is_running(self) -> bool:
        return self._running

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop(), name="escalation_worker")
        logger.info("escalation_worker_started", extra={"interval_sec": self.interval_sec})

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("escalation_worker_stopped")

    async def tick(self) -> dict[str, Any]:
        """Single processing pass — concurrent ticks serialize on the lock."""
        async with self._tick_lock:
            from services.escalation_service import escalation_service
            from services.owner_escalation_service import owner_escalation_service

            manager_result = await escalation_service.process_due_escalations()
            owner_result = await owner_escalation_service.check_overdue_requests()
            return {
                **manager_result,
                "owner_escalation": owner_result,
            }

    async def _loop(self) -> None:
        while self._running:
            try:
                result = await self.tick()
                if result.get("acted"):
                    logger.info("escalation_worker_tick", extra=result)
            except Exception:
                logger.warning("escalation_worker_tick_failed", exc_info=True)
            await asyncio.sleep(self.interval_sec)


_default_worker: EscalationWorker | None = None


def get_escalation_worker() -> EscalationWorker:
    global _default_worker
    if _default_worker is None:
        _default_worker = EscalationWorker()
    return _default_worker
