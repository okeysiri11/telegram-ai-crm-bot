# CRM Event Bus repository — PostgreSQL async persistence.

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.crm_events import (
    EVENT_STATUS_COMPLETED,
    EVENT_STATUS_FAILED,
    EVENT_STATUS_PENDING,
    EVENT_STATUS_PROCESSING,
    Event,
)
from database.seeds.event_registry import validate_event_type

logger = logging.getLogger(__name__)


class EventBusRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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

    async def claim_pending_events(self, *, limit: int = 50) -> list[Event]:
        result = await self._session.execute(
            select(Event)
            .where(Event.status == EVENT_STATUS_PENDING)
            .order_by(Event.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        events = list(result.scalars().all())
        now = datetime.now(timezone.utc)
        for event in events:
            event.status = EVENT_STATUS_PROCESSING
            state = dict(event.delivery_state or {})
            state["attempts"] = int(state.get("attempts", 0)) + 1
            event.delivery_state = state
            event.processed_at = now
        await self._session.flush()
        return events

    async def claim_failed_events(self, *, limit: int = 50) -> list[Event]:
        result = await self._session.execute(
            select(Event)
            .where(Event.status == EVENT_STATUS_FAILED)
            .order_by(Event.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        events = list(result.scalars().all())
        now = datetime.now(timezone.utc)
        for event in events:
            event.status = EVENT_STATUS_PROCESSING
            state = dict(event.delivery_state or {})
            state["attempts"] = int(state.get("attempts", 0)) + 1
            event.delivery_state = state
            event.processed_at = now
        await self._session.flush()
        return events

    async def mark_completed(self, event: Event, handler_names: list[str]) -> None:
        state = dict(event.delivery_state or {})
        done = set(state.get("handlers_done") or [])
        done.update(handler_names)
        state["handlers_done"] = sorted(done)
        event.delivery_state = state
        event.status = EVENT_STATUS_COMPLETED
        event.processed_at = datetime.now(timezone.utc)
        await self._session.flush()
        logger.info(
            "event_completed",
            extra={"event_id": str(event.id), "event_type": event.event_type},
        )

    async def mark_failed(self, event: Event, error: str) -> None:
        state = dict(event.delivery_state or {})
        state["last_error"] = error
        event.delivery_state = state
        event.status = EVENT_STATUS_FAILED
        event.processed_at = datetime.now(timezone.utc)
        await self._session.flush()
        logger.error(
            "event_failed",
            extra={
                "event_id": str(event.id),
                "event_type": event.event_type,
                "error": error,
            },
        )

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
        event.delivery_state = state
        event.processed_at = None
        await self._session.flush()
