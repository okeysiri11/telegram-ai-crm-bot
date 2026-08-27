"""Background retry worker for Vanguard tracking delivery.

Bounded exponential backoff. Exhausted retries become DEAD_LETTER.
Does not busy-loop WAITING_PROVIDER destinations.
Does not fabricate DELIVERED.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Awaitable, Callable

from services.recruiting_ops.tracking_lifecycle import (
    DEAD_LETTER,
    DELIVERED,
    MAX_ATTEMPTS,
    PENDING,
    PROCESSING,
    RETRYING,
    WAITING_PROVIDER,
    classify_lifecycle,
    iso_now,
    is_due,
    next_attempt_at,
    normalize_status,
    provider_is_configured,
)
from services.recruiting_ops.tracking_adapters import PROVIDER_DESTINATIONS, destination_of

logger = logging.getLogger(__name__)

PersistFn = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]
TickFn = Callable[[], Awaitable[Any]]


class TrackingWorker:
    def __init__(self) -> None:
        self.pending: list[dict[str, Any]] = []
        self.enabled = True
        self._loop_task: asyncio.Task[None] | None = None
        self._tick_fn: TickFn | None = None

    def snapshot(self) -> dict[str, Any]:
        retrying = sum(1 for item in self.pending if normalize_status(item.get("delivery_status")) == RETRYING)
        failed = sum(1 for item in self.pending if normalize_status(item.get("delivery_status")) == DEAD_LETTER)
        waiting = sum(1 for item in self.pending if normalize_status(item.get("delivery_status")) == WAITING_PROVIDER)
        processing = sum(1 for item in self.pending if normalize_status(item.get("delivery_status")) == PROCESSING)
        stamps = [str(item.get("created_at") or item.get("enqueued_at") or "") for item in self.pending]
        oldest = min((s for s in stamps if s), default=None)
        return {
            "enabled": self.enabled,
            "pending": len(self.pending),
            "processing": processing,
            "retrying": retrying,
            "waiting_provider": waiting,
            "failed": failed,
            "dead_letter": failed,
            "max_attempts": MAX_ATTEMPTS,
            "oldest_pending": oldest,
        }

    def enqueue(self, event: dict[str, Any]) -> dict[str, Any]:
        item = dict(event)
        dest = destination_of(item)
        if dest in PROVIDER_DESTINATIONS and not provider_is_configured(dest):
            item["delivery_status"] = WAITING_PROVIDER
            item["delivery_class"] = "waiting_provider"
            item["provider_status"] = "NOT_CONFIGURED"
        else:
            item["delivery_status"] = RETRYING
        item["attempt"] = int(item.get("attempt") or 0)
        item["enqueued_at"] = item.get("enqueued_at") or iso_now()
        eid = str(item.get("event_id") or item.get("id") or "")
        if eid:
            self.pending = [p for p in self.pending if str(p.get("event_id") or p.get("id") or "") != eid]
        self.pending.append(item)
        return item

    def sync_with(self, events: list[dict[str, Any]]) -> None:
        by_id = {str(item.get("event_id") or item.get("id") or ""): item for item in events}
        remaining: list[dict[str, Any]] = []
        for pending in self.pending:
            eid = str(pending.get("event_id") or pending.get("id") or "")
            current = by_id.get(eid)
            status = classify_lifecycle(current or pending)
            if status in {DELIVERED, DEAD_LETTER}:
                continue
            remaining.append(current or pending)
        self.pending = remaining
        self.rehydrate(events)

    def rehydrate(self, events: list[dict[str, Any]]) -> int:
        added = 0
        known = {str(p.get("event_id") or p.get("id") or "") for p in self.pending}
        for event in events:
            status = classify_lifecycle(event)
            if status not in {RETRYING, PENDING, PROCESSING, WAITING_PROVIDER}:
                continue
            eid = str(event.get("event_id") or event.get("id") or "")
            if eid and eid in known:
                continue
            self.pending.append(dict(event))
            if eid:
                known.add(eid)
            added += 1
        return added

    async def tick(self, persist: PersistFn, *, force: bool = False) -> list[dict[str, Any]]:
        if not self.pending:
            return []
        remaining: list[dict[str, Any]] = []
        done: list[dict[str, Any]] = []
        for item in list(self.pending):
            dest = destination_of(item)
            status = normalize_status(item.get("delivery_status"))
            if status == DEAD_LETTER:
                remaining.append(item)
                continue
            if dest in PROVIDER_DESTINATIONS and not provider_is_configured(dest):
                item["delivery_status"] = WAITING_PROVIDER
                remaining.append(item)
                continue
            if dest in PROVIDER_DESTINATIONS and status == WAITING_PROVIDER and provider_is_configured(dest):
                item["delivery_status"] = RETRYING
                item["next_attempt_at"] = iso_now()
            if not force and not is_due(item):
                remaining.append(item)
                continue
            item["attempt"] = int(item.get("attempt") or 0) + 1
            item["delivery_status"] = PROCESSING
            item["last_attempt_at"] = iso_now()
            try:
                saved = await persist(item)
                saved["delivery_status"] = DELIVERED
                saved["attempt"] = item["attempt"]
                saved["last_error"] = None
                done.append(saved)
            except Exception as exc:
                logger.warning("tracking worker persist failed attempt=%s: %s", item["attempt"], exc)
                item["last_error"] = str(exc)
                item["error"] = "tracking_failed"
                if item["attempt"] >= MAX_ATTEMPTS:
                    item["delivery_status"] = DEAD_LETTER
                    item["dead_letter_reason"] = "max_attempts_exceeded"
                    item["message_ru"] = "Событие не доставлено (исчерпаны повторы)."
                    remaining.append(item)
                    done.append(item)
                else:
                    item["delivery_status"] = RETRYING
                    item["next_attempt_at"] = next_attempt_at(item["attempt"])
                    remaining.append(item)
        self.pending = remaining
        return done

    def ensure_loop(self, tick_fn: TickFn) -> None:
        if os.environ.get("PYTEST_CURRENT_TEST"):
            return
        self._tick_fn = tick_fn
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        if self._loop_task is not None and not self._loop_task.done():
            return
        self._loop_task = loop.create_task(self._run_loop())

    async def _run_loop(self) -> None:
        while self.enabled:
            try:
                if self._tick_fn is not None:
                    await self._tick_fn()
            except Exception:
                logger.exception("tracking worker loop tick failed")
            await asyncio.sleep(5)

    def reset(self) -> None:
        self.pending.clear()
        if self._loop_task is not None:
            self._loop_task.cancel()
            self._loop_task = None
        self._tick_fn = None


_WORKER = TrackingWorker()


def get_tracking_worker() -> TrackingWorker:
    return _WORKER


def reset_tracking_worker_for_tests() -> None:
    _WORKER.reset()
