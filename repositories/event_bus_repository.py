# CRM Event Bus repository — PostgreSQL async persistence.

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import cast, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.types import Integer

from database.models.crm_events import (
    EVENT_STATUS_COMPLETED,
    EVENT_STATUS_DEAD_LETTER,
    EVENT_STATUS_FAILED,
    EVENT_STATUS_PENDING,
    EVENT_STATUS_PROCESSING,
    Event,
)
from database.models.event_dead_letter import EventDeadLetter
from database.seeds.event_registry import validate_event_type
from services.event_bus_config import MAX_RETRIES, compute_backoff_seconds

logger = logging.getLogger(__name__)


class EventBusRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _attempts(state: dict[str, Any]) -> int:
        return int(state.get("attempts", 0))

    @staticmethod
    def _next_retry_at(state: dict[str, Any]) -> datetime | None:
        raw = state.get("next_retry_at")
        if not raw:
            return None
        return datetime.fromisoformat(raw)

    async def find_duplicate(
        self,
        *,
        event_type: str,
        aggregate_type: str,
        aggregate_id: uuid.UUID,
        correlation_id: uuid.UUID,
    ) -> Event | None:
        result = await self._session.execute(
            select(Event).where(
                Event.event_type == event_type,
                Event.aggregate_type == aggregate_type,
                Event.aggregate_id == aggregate_id,
                Event.correlation_id == correlation_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_event(
        self,
        *,
        event_type: str,
        aggregate_type: str,
        aggregate_id: uuid.UUID,
        payload: dict[str, Any],
        correlation_id: uuid.UUID,
        causation_id: uuid.UUID | None = None,
    ) -> Event:
        validate_event_type(event_type)
        event = Event(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload,
            correlation_id=correlation_id,
            causation_id=causation_id,
            status=EVENT_STATUS_PENDING,
            delivery_state={"handlers_done": [], "attempts": 0},
        )
        self._session.add(event)
        await self._session.flush()
        logger.info(
            "event_published",
            extra={
                "event_id": str(event.id),
                "event_type": event_type,
                "aggregate_type": aggregate_type,
                "aggregate_id": str(aggregate_id),
                "correlation_id": str(correlation_id),
            },
        )
        return event

    async def publish_event(
        self,
        *,
        event_type: str,
        aggregate_type: str,
        aggregate_id: uuid.UUID,
        payload: dict[str, Any] | None = None,
        correlation_id: uuid.UUID | None = None,
        causation_id: uuid.UUID | None = None,
    ) -> Event:
        corr = correlation_id or uuid.uuid4()
        existing = await self.find_duplicate(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            correlation_id=corr,
        )
        if existing is not None:
            logger.info(
                "event_duplicate_detected",
                extra={
                    "event_id": str(existing.id),
                    "event_type": event_type,
                    "correlation_id": str(corr),
                },
            )
            return existing

        try:
            async with self._session.begin_nested():
                return await self.create_event(
                    event_type=event_type,
                    aggregate_type=aggregate_type,
                    aggregate_id=aggregate_id,
                    payload=payload or {},
                    correlation_id=corr,
                    causation_id=causation_id,
                )
        except IntegrityError:
            duplicate = await self.find_duplicate(
                event_type=event_type,
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                correlation_id=corr,
            )
            if duplicate is not None:
                logger.info(
                    "event_duplicate_detected",
                    extra={
                        "event_id": str(duplicate.id),
                        "event_type": event_type,
                        "correlation_id": str(corr),
                    },
                )
                return duplicate
            raise

    async def count_pending_events(self) -> int:
        result = await self._session.scalar(
            select(func.count())
            .select_from(Event)
            .where(Event.status == EVENT_STATUS_PENDING)
        )
        return int(result or 0)

    async def count_queue_size(self) -> dict[str, int]:
        pending = await self._session.scalar(
            select(func.count())
            .select_from(Event)
            .where(Event.status == EVENT_STATUS_PENDING)
        )
        processing = await self._session.scalar(
            select(func.count())
            .select_from(Event)
            .where(Event.status == EVENT_STATUS_PROCESSING)
        )
        failed = await self._session.scalar(
            select(func.count())
            .select_from(Event)
            .where(Event.status == EVENT_STATUS_FAILED)
        )
        return {
            "pending": int(pending or 0),
            "processing": int(processing or 0),
            "failed": int(failed or 0),
            "total": int(pending or 0) + int(processing or 0) + int(failed or 0),
        }

    async def claim_pending_events(self, *, limit: int = 50) -> list[Event]:
        return await self._claim_events(
            statuses=(EVENT_STATUS_PENDING,),
            limit=limit,
            check_backoff=False,
        )

    async def claim_failed_events(self, *, limit: int = 50) -> list[Event]:
        return await self._claim_events(
            statuses=(EVENT_STATUS_FAILED,),
            limit=limit,
            check_backoff=True,
        )

    async def claim_events_for_processing(
        self,
        *,
        limit: int = 50,
        max_retries: int = MAX_RETRIES,
    ) -> list[Event]:
        now = datetime.now(timezone.utc)
        attempts_expr = cast(
            func.coalesce(Event.delivery_state["attempts"].as_string(), "0"),
            Integer,
        )
        result = await self._session.execute(
            select(Event)
            .where(
                or_(
                    Event.status == EVENT_STATUS_PENDING,
                    (
                        (Event.status == EVENT_STATUS_FAILED)
                        & (attempts_expr < max_retries)
                    ),
                )
            )
            .order_by(Event.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        events = list(result.scalars().all())
        claimed: list[Event] = []
        for event in events:
            state = dict(event.delivery_state or {})
            if event.status == EVENT_STATUS_FAILED:
                next_retry = self._next_retry_at(state)
                if next_retry is not None and next_retry > now:
                    continue
                state["handlers_done"] = []
            state["attempts"] = self._attempts(state) + 1
            state["processing_started_at"] = now.isoformat()
            event.delivery_state = state
            event.status = EVENT_STATUS_PROCESSING
            event.processed_at = now
            claimed.append(event)
        await self._session.flush()
        return claimed

    async def _claim_events(
        self,
        *,
        statuses: tuple[str, ...],
        limit: int,
        check_backoff: bool,
    ) -> list[Event]:
        now = datetime.now(timezone.utc)
        result = await self._session.execute(
            select(Event)
            .where(Event.status.in_(statuses))
            .order_by(Event.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        events = list(result.scalars().all())
        claimed: list[Event] = []
        for event in events:
            state = dict(event.delivery_state or {})
            if check_backoff:
                next_retry = self._next_retry_at(state)
                if next_retry is not None and next_retry > now:
                    continue
                if self._attempts(state) >= MAX_RETRIES:
                    continue
                state["handlers_done"] = []
            state["attempts"] = self._attempts(state) + 1
            state["processing_started_at"] = now.isoformat()
            event.delivery_state = state
            event.status = EVENT_STATUS_PROCESSING
            event.processed_at = now
            claimed.append(event)
        await self._session.flush()
        return claimed

    async def mark_completed(self, event: Event, handler_names: list[str]) -> None:
        state = dict(event.delivery_state or {})
        done = set(state.get("handlers_done") or [])
        done.update(handler_names)
        state["handlers_done"] = sorted(done)
        state.pop("last_error", None)
        state.pop("next_retry_at", None)
        event.delivery_state = state
        event.status = EVENT_STATUS_COMPLETED
        event.processed_at = datetime.now(timezone.utc)
        await self._session.flush()
        logger.info(
            "event_completed",
            extra={"event_id": str(event.id), "event_type": event.event_type},
        )

    async def mark_failed(
        self,
        event: Event,
        error: str,
        *,
        max_retries: int = MAX_RETRIES,
    ) -> str:
        state = dict(event.delivery_state or {})
        attempts = self._attempts(state)
        state["last_error"] = error
        event.delivery_state = state
        event.processed_at = datetime.now(timezone.utc)

        if attempts >= max_retries:
            await self.move_to_dead_letter(event, error, retry_count=attempts)
            return EVENT_STATUS_DEAD_LETTER

        backoff = compute_backoff_seconds(attempts)
        next_retry = datetime.now(timezone.utc) + timedelta(seconds=backoff)
        state["next_retry_at"] = next_retry.isoformat()
        event.delivery_state = state
        event.status = EVENT_STATUS_FAILED
        await self._session.flush()
        logger.warning(
            "event_failed_will_retry",
            extra={
                "event_id": str(event.id),
                "event_type": event.event_type,
                "error": error,
                "attempts": attempts,
                "max_retries": max_retries,
                "next_retry_at": state["next_retry_at"],
            },
        )
        return EVENT_STATUS_FAILED

    async def move_to_dead_letter(
        self,
        event: Event,
        error_message: str,
        *,
        retry_count: int | None = None,
    ) -> EventDeadLetter:
        attempts = retry_count if retry_count is not None else self._attempts(
            event.delivery_state or {}
        )
        dead_letter = EventDeadLetter(
            event_name=event.event_type,
            payload={
                "event_id": str(event.id),
                "aggregate_type": event.aggregate_type,
                "aggregate_id": str(event.aggregate_id),
                "correlation_id": str(event.correlation_id),
                "causation_id": str(event.causation_id) if event.causation_id else None,
                "original_payload": dict(event.payload),
                "delivery_state": dict(event.delivery_state or {}),
            },
            error_message=error_message,
            retry_count=attempts,
        )
        self._session.add(dead_letter)
        event.status = EVENT_STATUS_DEAD_LETTER
        state = dict(event.delivery_state or {})
        state["last_error"] = error_message
        state["dead_letter_id"] = str(dead_letter.id)
        event.delivery_state = state
        event.processed_at = datetime.now(timezone.utc)
        await self._session.flush()
        logger.error(
            "event_moved_to_dead_letter",
            extra={
                "event_id": str(event.id),
                "dead_letter_id": str(dead_letter.id),
                "event_type": event.event_type,
                "retry_count": attempts,
            },
        )
        return dead_letter

    async def list_by_aggregate(self, aggregate_id: uuid.UUID) -> list[Event]:
        result = await self._session.execute(
            select(Event)
            .where(Event.aggregate_id == aggregate_id)
            .order_by(Event.created_at.asc())
        )
        return list(result.scalars().all())

    async def reset_for_replay(self, event: Event) -> Event:
        replay = Event(
            event_type=event.event_type,
            aggregate_type=event.aggregate_type,
            aggregate_id=event.aggregate_id,
            payload=dict(event.payload),
            correlation_id=uuid.uuid4(),
            causation_id=event.id,
            status=EVENT_STATUS_PENDING,
            delivery_state={"handlers_done": [], "attempts": 0, "replay_of": str(event.id)},
        )
        self._session.add(replay)
        await self._session.flush()
        logger.info(
            "event_replay_created",
            extra={
                "source_event_id": str(event.id),
                "replay_event_id": str(replay.id),
                "aggregate_id": str(event.aggregate_id),
            },
        )
        return replay

    async def reset_failed_to_pending(self, event: Event) -> None:
        event.status = EVENT_STATUS_PENDING
        state = dict(event.delivery_state or {})
        state["handlers_done"] = []
        state.pop("next_retry_at", None)
        event.delivery_state = state
        event.processed_at = None
        await self._session.flush()
