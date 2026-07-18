# Retry manager — exponential backoff, DLQ, history.

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from platform_integrations.exceptions import RetryExhaustedError
from platform_integrations.integration_events import RetryScheduledEvent
from platform_integrations.models import RetryRecord

logger = logging.getLogger(__name__)

DEFAULT_MAX_ATTEMPTS = 5
DEFAULT_BASE_DELAY = 1.0
DEFAULT_MAX_DELAY = 60.0


class RetryManager:
    def __init__(self) -> None:
        self._pending: dict[str, RetryRecord] = {}
        self._history: list[RetryRecord] = []
        self._dead_letter: list[dict[str, Any]] = []

    def reset(self) -> None:
        self._pending.clear()
        self._history.clear()
        self._dead_letter.clear()

    def schedule(
        self,
        *,
        connector_id: str,
        operation: str,
        payload: dict[str, Any],
        attempt: int = 1,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        error: str | None = None,
    ) -> RetryRecord:
        if attempt > max_attempts:
            self._dead_letter.append(
                {
                    "connector_id": connector_id,
                    "operation": operation,
                    "payload": payload,
                    "error": error,
                    "attempts": attempt - 1,
                }
            )
            raise RetryExhaustedError(
                f"Retry exhausted for {connector_id}/{operation} after {max_attempts} attempts"
            )

        delay = min(DEFAULT_BASE_DELAY * (2 ** (attempt - 1)), DEFAULT_MAX_DELAY)
        record = RetryRecord(
            retry_id=str(uuid.uuid4()),
            connector_id=connector_id,
            operation=operation,
            payload=payload,
            attempt=attempt,
            max_attempts=max_attempts,
            next_retry_at=time.monotonic() + delay,
            error=error,
        )
        self._pending[record.retry_id] = record
        self._history.append(record)
        logger.info(
            "retry_scheduled id=%s connector=%s attempt=%s delay=%.1fs",
            record.retry_id,
            connector_id,
            attempt,
            delay,
        )
        return record

    async def publish_scheduled(self, record: RetryRecord) -> None:
        from events.event_bus import publish

        await publish(
            RetryScheduledEvent(
                retry_id=record.retry_id,
                connector_id=record.connector_id,
                operation=record.operation,
                attempt=record.attempt,
                next_retry_at=record.next_retry_at,
            )
        )

    def due_retries(self) -> list[RetryRecord]:
        now = time.monotonic()
        due = [r for r in self._pending.values() if r.next_retry_at <= now]
        for record in due:
            self._pending.pop(record.retry_id, None)
        return due

    def complete(self, retry_id: str) -> None:
        record = self._pending.pop(retry_id, None)
        if record:
            record.status = "completed"

    def history(self, *, limit: int = 100) -> list[RetryRecord]:
        return self._history[-limit:]

    def dead_letter_queue(self) -> list[dict[str, Any]]:
        return list(self._dead_letter)


retry_manager = RetryManager()
