# CRM Event Bus — async PostgreSQL event publishing and processing.

from __future__ import annotations

import inspect
import logging
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from database.seeds.event_registry import validate_event_type
from database.session import get_session
from repositories.event_bus_repository import EventBusRepository

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
        return event.id


async def _dispatch_event(repo: EventBusRepository, event) -> bool:
    handlers = _handlers.get(event.event_type, [])
    if not handlers:
        await repo.mark_completed(event, [])
        return True

    state = dict(event.delivery_state or {})
    done = set(state.get("handlers_done") or [])
    succeeded: list[str] = []

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
            result = handler(event)
            if inspect.isawaitable(result):
                await result
            succeeded.append(handler_id)
        except Exception as exc:
            await repo.mark_failed(event, f"{handler_id}: {exc}")
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
    return True


async def process_pending_events(*, limit: int = 50) -> dict[str, int]:
    stats = {"claimed": 0, "completed": 0, "failed": 0}
    async with get_session() as session:
        repo = EventBusRepository(session)
        events = await repo.claim_pending_events(limit=limit)
        stats["claimed"] = len(events)
        for event in events:
            ok = await _dispatch_event(repo, event)
            if ok:
                stats["completed"] += 1
            else:
                stats["failed"] += 1
    return stats


async def retry_failed_events(*, limit: int = 50) -> dict[str, int]:
    stats = {"claimed": 0, "completed": 0, "failed": 0}
    async with get_session() as session:
        repo = EventBusRepository(session)
        failed = await repo.claim_failed_events(limit=limit)
        stats["claimed"] = len(failed)
        for event in failed:
            state = dict(event.delivery_state or {})
            state["handlers_done"] = []
            event.delivery_state = state
            ok = await _dispatch_event(repo, event)
            if ok:
                stats["completed"] += 1
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
