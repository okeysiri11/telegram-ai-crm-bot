# CRM Event Bus — async PostgreSQL event publishing and processing.

from __future__ import annotations

import asyncio
import inspect
import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from database.models.crm_events import EVENT_STATUS_DEAD_LETTER, EVENT_STATUS_FAILED
from database.seeds.event_registry import validate_event_type
from database.session import get_session
from repositories.event_bus_repository import EventBusRepository
from services.event_bus_config import (
    DEFAULT_WORKER_COUNT,
    HANDLER_TIMEOUT_SECONDS,
    MAX_RETRIES,
    POLL_INTERVAL_SECONDS,
)
from services import event_bus_metrics as metrics

logger = logging.getLogger(__name__)

EventHandler = Callable[..., Awaitable[None] | None]

_handlers: dict[str, list[tuple[str, EventHandler]]] = {}


def subscribe(
    event_type: str,
    handler: EventHandler,
    *,
    handler_id: str | None = None,
) -> str:
    validate_event_type(event_type)
    name = handler_id or getattr(handler, "__name__", "handler")
    bucket = _handlers.setdefault(event_type, [])
    for existing_id, _ in bucket:
        if existing_id == name:
            bucket[:] = [(hid, fn) for hid, fn in bucket if hid != name]
            break
    bucket.append((name, handler))
    logger.info(
        "event_handler_subscribed",
        extra={"event_type": event_type, "handler_id": name},
    )
    return name


def list_subscribers(event_type: str | None = None) -> dict[str, list[str]]:
    if event_type is not None:
        return {event_type: [hid for hid, _ in _handlers.get(event_type, [])]}
    return {key: [hid for hid, _ in items] for key, items in _handlers.items()}


async def publish_event(
    event_type: str,
    aggregate_type: str,
    aggregate_id: uuid.UUID,
    payload: dict[str, Any] | None = None,
    correlation_id: uuid.UUID | None = None,
    causation_id: uuid.UUID | None = None,
    *,
    session: AsyncSession | None = None,
) -> uuid.UUID:
    validate_event_type(event_type)

    if session is not None:
        repo = EventBusRepository(session)
        event = await repo.publish_event(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
        metrics.record_published()
        return event.id

    async with get_session() as owned_session:
        repo = EventBusRepository(owned_session)
        event = await repo.publish_event(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload,
            correlation_id=correlation_id,
            causation_id=causation_id,
        )
        metrics.record_published()
        return event.id


async def _invoke_handler(
    handler: EventHandler,
    event,
    *,
    timeout_seconds: float,
) -> None:
    result = handler(event)
    if inspect.isawaitable(result):
        await asyncio.wait_for(result, timeout=timeout_seconds)
    elif timeout_seconds and timeout_seconds > 0:
        pass


async def _dispatch_event(
    repo: EventBusRepository,
    event,
    *,
    timeout_seconds: float = HANDLER_TIMEOUT_SECONDS,
    max_retries: int = MAX_RETRIES,
) -> bool:
    handlers = _handlers.get(event.event_type, [])
    if not handlers:
        await repo.mark_completed(event, [])
        return True

    state = dict(event.delivery_state or {})
    done = set(state.get("handlers_done") or [])
    succeeded: list[str] = []
    started = time.perf_counter()

    for handler_id, handler in handlers:
        if handler_id in done:
            logger.info(
                "event_handler_skipped",
                extra={
                    "event_id": str(event.id),
                    "handler_id": handler_id,
                    "reason": "already_processed",
                },
            )
            continue
        try:
            await _invoke_handler(
                handler,
                event,
                timeout_seconds=timeout_seconds,
            )
            succeeded.append(handler_id)
        except asyncio.TimeoutError:
            error = f"{handler_id}: handler timed out after {timeout_seconds}s"
            status = await repo.mark_failed(event, error, max_retries=max_retries)
            metrics.record_failure()
            if status == EVENT_STATUS_DEAD_LETTER:
                metrics.record_dead_letter()
            logger.error(
                "event_handler_timeout",
                extra={
                    "event_id": str(event.id),
                    "handler_id": handler_id,
                    "event_type": event.event_type,
                    "timeout_seconds": timeout_seconds,
                },
            )
            return False
        except Exception as exc:
            error = f"{handler_id}: {exc}"
            status = await repo.mark_failed(event, error, max_retries=max_retries)
            metrics.record_failure()
            if status == EVENT_STATUS_DEAD_LETTER:
                metrics.record_dead_letter()
            logger.exception(
                "event_handler_error",
                extra={
                    "event_id": str(event.id),
                    "handler_id": handler_id,
                    "event_type": event.event_type,
                },
            )
            return False

    await repo.mark_completed(event, succeeded)
    elapsed_ms = (time.perf_counter() - started) * 1000
    metrics.record_success(elapsed_ms)
    return True


async def process_pending_events(
    *,
    limit: int = 50,
    timeout_seconds: float = HANDLER_TIMEOUT_SECONDS,
    max_retries: int = MAX_RETRIES,
) -> dict[str, int]:
    stats = {"claimed": 0, "completed": 0, "failed": 0, "dead_letter": 0}
    async with get_session() as session:
        repo = EventBusRepository(session)
        events = await repo.claim_events_for_processing(
            limit=limit,
            max_retries=max_retries,
        )
        stats["claimed"] = len(events)
        for event in events:
            ok = await _dispatch_event(
                repo,
                event,
                timeout_seconds=timeout_seconds,
                max_retries=max_retries,
            )
            if ok:
                stats["completed"] += 1
            elif event.status == EVENT_STATUS_DEAD_LETTER:
                stats["dead_letter"] += 1
            else:
                stats["failed"] += 1
    return stats


async def retry_failed_events(
    *,
    limit: int = 50,
    timeout_seconds: float = HANDLER_TIMEOUT_SECONDS,
    max_retries: int = MAX_RETRIES,
) -> dict[str, int]:
    stats = {"claimed": 0, "completed": 0, "failed": 0, "dead_letter": 0}
    async with get_session() as session:
        repo = EventBusRepository(session)
        failed = await repo.claim_failed_events(limit=limit)
        stats["claimed"] = len(failed)
        for event in failed:
            ok = await _dispatch_event(
                repo,
                event,
                timeout_seconds=timeout_seconds,
                max_retries=max_retries,
            )
            if ok:
                stats["completed"] += 1
            elif event.status == EVENT_STATUS_DEAD_LETTER:
                stats["dead_letter"] += 1
            else:
                stats["failed"] += 1
    return stats


async def replay_events(aggregate_id: uuid.UUID) -> list[uuid.UUID]:
    replay_ids: list[uuid.UUID] = []
    async with get_session() as session:
        repo = EventBusRepository(session)
        source_events = await repo.list_by_aggregate(aggregate_id)
        for source in source_events:
            replay = await repo.reset_for_replay(source)
            replay_ids.append(replay.id)
    logger.info(
        "events_replay_scheduled",
        extra={"aggregate_id": str(aggregate_id), "count": len(replay_ids)},
    )
    return replay_ids


async def get_queue_size() -> dict[str, int]:
    async with get_session() as session:
        repo = EventBusRepository(session)
        return await repo.count_queue_size()


async def get_metrics() -> dict:
    return await metrics.get_metrics()


class EventBusWorker:
    """Background worker pool for event processing with graceful shutdown."""

    def __init__(
        self,
        *,
        worker_count: int = DEFAULT_WORKER_COUNT,
        poll_interval_seconds: float = POLL_INTERVAL_SECONDS,
        batch_size: int = 25,
        timeout_seconds: float = HANDLER_TIMEOUT_SECONDS,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        self.worker_count = worker_count
        self.poll_interval_seconds = poll_interval_seconds
        self.batch_size = batch_size
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._tasks: list[asyncio.Task] = []
        self._shutdown = asyncio.Event()
        self._started = False

    @property
    def is_running(self) -> bool:
        return self._started and not self._shutdown.is_set()

    async def start(self) -> None:
        if self._started:
            return
        self._shutdown.clear()
        self._started = True
        for index in range(self.worker_count):
            task = asyncio.create_task(
                self._worker_loop(index),
                name=f"event-bus-worker-{index}",
            )
            self._tasks.append(task)
        logger.info(
            "event_bus_workers_started",
            extra={"worker_count": self.worker_count},
        )

    async def shutdown(self, *, wait: bool = True) -> None:
        if not self._started:
            return
        self._shutdown.set()
        if wait and self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        self._started = False
        logger.info("event_bus_workers_stopped")

    async def get_queue_size(self) -> dict[str, int]:
        return await get_queue_size()

    async def _worker_loop(self, worker_id: int) -> None:
        logger.info("event_bus_worker_started", extra={"worker_id": worker_id})
        while not self._shutdown.is_set():
            try:
                stats = await process_pending_events(
                    limit=self.batch_size,
                    timeout_seconds=self.timeout_seconds,
                    max_retries=self.max_retries,
                )
                if stats["claimed"] == 0:
                    try:
                        await asyncio.wait_for(
                            self._shutdown.wait(),
                            timeout=self.poll_interval_seconds,
                        )
                    except asyncio.TimeoutError:
                        pass
                else:
                    logger.debug(
                        "event_bus_worker_batch",
                        extra={"worker_id": worker_id, **stats},
                    )
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception(
                    "event_bus_worker_error",
                    extra={"worker_id": worker_id},
                )
                try:
                    await asyncio.wait_for(
                        self._shutdown.wait(),
                        timeout=self.poll_interval_seconds,
                    )
                except asyncio.TimeoutError:
                    pass
        logger.info("event_bus_worker_stopped", extra={"worker_id": worker_id})


_default_worker: EventBusWorker | None = None


def get_default_worker() -> EventBusWorker:
    global _default_worker
    if _default_worker is None:
        _default_worker = EventBusWorker()
    return _default_worker
