"""Background retry worker for Vanguard tracking delivery.

Does not fabricate DELIVERED. Exhausted retries become terminal FAILED.
"""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5
PersistFn = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


class TrackingWorker:
    def __init__(self) -> None:
        self.pending: list[dict[str, Any]] = []
        self.enabled = True

    def snapshot(self) -> dict[str, Any]:
        retrying = sum(1 for item in self.pending if item.get("delivery_status") == "RETRYING")
        failed = sum(1 for item in self.pending if item.get("delivery_status") == "FAILED")
        return {
            "enabled": self.enabled,
            "pending": len(self.pending),
            "retrying": retrying,
            "failed": failed,
            "max_attempts": MAX_ATTEMPTS,
        }

    def enqueue(self, event: dict[str, Any]) -> dict[str, Any]:
        item = dict(event)
        item["delivery_status"] = "RETRYING"
        item["attempt"] = int(item.get("attempt") or 0)
        self.pending.append(item)
        return item

    async def tick(self, persist: PersistFn) -> list[dict[str, Any]]:
        if not self.pending:
            return []
        remaining: list[dict[str, Any]] = []
        done: list[dict[str, Any]] = []
        for item in list(self.pending):
            if item.get("delivery_status") == "FAILED":
                remaining.append(item)
                continue
            item["attempt"] = int(item.get("attempt") or 0) + 1
            item["delivery_status"] = "RETRYING"
            try:
                saved = await persist(item)
                saved["delivery_status"] = "DELIVERED"
                saved["attempt"] = item["attempt"]
                done.append(saved)
            except Exception as exc:
                logger.warning("tracking worker persist failed attempt=%s: %s", item["attempt"], exc)
                if item["attempt"] >= MAX_ATTEMPTS:
                    item["delivery_status"] = "FAILED"
                    item["error"] = "tracking_failed"
                    item["message_ru"] = "Событие не доставлено"
                    remaining.append(item)
                    done.append(item)
                else:
                    remaining.append(item)
        self.pending = remaining
        return done

    def reset(self) -> None:
        self.pending.clear()


_WORKER = TrackingWorker()


def get_tracking_worker() -> TrackingWorker:
    return _WORKER


def reset_tracking_worker_for_tests() -> None:
    _WORKER.reset()
