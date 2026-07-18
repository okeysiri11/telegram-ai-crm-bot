# Queue manager — async operation queue for integrations.

from __future__ import annotations

import asyncio
import logging
from collections import deque

from platform_integrations.models import QueuedOperation

logger = logging.getLogger(__name__)


class QueueManager:
    def __init__(self, *, max_size: int = 10_000) -> None:
        self._queue: deque[QueuedOperation] = deque()
        self._lock = asyncio.Lock()
        self._max_size = max_size

    def reset(self) -> None:
        self._queue.clear()

    async def enqueue(self, connector_id: str, operation: str, payload: dict) -> QueuedOperation:
        async with self._lock:
            if len(self._queue) >= self._max_size:
                self._queue.popleft()
            item = QueuedOperation.new(connector_id, operation, payload)
            self._queue.append(item)
            logger.debug("integration_queued id=%s connector=%s", item.operation_id, connector_id)
            return item

    async def dequeue(self) -> QueuedOperation | None:
        async with self._lock:
            if not self._queue:
                return None
            return self._queue.popleft()

    async def size(self) -> int:
        async with self._lock:
            return len(self._queue)

    async def snapshot(self) -> list[dict]:
        async with self._lock:
            return [
                {
                    "operation_id": op.operation_id,
                    "connector_id": op.connector_id,
                    "operation": op.operation,
                }
                for op in list(self._queue)[:50]
            ]


queue_manager = QueueManager()
