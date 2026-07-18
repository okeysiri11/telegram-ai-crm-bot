# SlaTimerService — create and update request_sla records from EventBus events.

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone

from database.session import get_session
from events.base_event import BaseEvent
from events.request_events import (
    ManagerFirstResponseEvent,
    RequestAssignedEvent,
    RequestCompletedEvent,
)
from repositories.escalation_repository import EscalationRepository

logger = logging.getLogger(__name__)

_subscribed = False

SLA_FIRST_RESPONSE_SEC = int(os.getenv("SLA_FIRST_RESPONSE_SEC", str(30 * 60)))
SLA_CLOSE_SEC = int(os.getenv("SLA_CLOSE_SEC", str(72 * 3600)))


class SlaTimerService:
    @staticmethod
    def _enqueue(coro) -> None:
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(coro)
            task.add_done_callback(_log_task_error)
        except RuntimeError:
            try:
                asyncio.run(coro)
            except Exception:
                logger.warning("sla_timer_service sync fallback failed", exc_info=True)

    @staticmethod
    async def handle_event(event: BaseEvent) -> None:
        SlaTimerService._enqueue(SlaTimerService._process_event(event))

    @staticmethod
    async def _process_event(event: BaseEvent) -> None:
        try:
            if isinstance(event, RequestAssignedEvent):
                await SlaTimerService._on_assigned(event)
            elif isinstance(event, ManagerFirstResponseEvent):
                await SlaTimerService._on_first_response(event)
            elif isinstance(event, RequestCompletedEvent):
                await SlaTimerService._on_completed(event)
        except Exception:
            logger.warning(
                "sla_timer_event_failed",
                extra={"event_type": event.event_type, "event_id": event.event_id},
                exc_info=True,
            )

    @staticmethod
    async def _on_assigned(event: RequestAssignedEvent) -> None:
        assigned_at = event.occurred_at or datetime.now(timezone.utc)
        first_deadline = assigned_at + timedelta(seconds=SLA_FIRST_RESPONSE_SEC)
        completion_deadline = assigned_at + timedelta(seconds=SLA_CLOSE_SEC)

        async with get_session() as session:
            await EscalationRepository(session).create_sla(
                request_id=event.request_id,
                manager_telegram_id=event.manager_telegram_id,
                first_response_deadline=first_deadline,
                completion_deadline=completion_deadline,
                assigned_at=assigned_at,
            )

    @staticmethod
    async def _on_first_response(event: ManagerFirstResponseEvent) -> None:
        responded_at = event.occurred_at or datetime.now(timezone.utc)
        async with get_session() as session:
            await EscalationRepository(session).mark_first_response(
                event.request_id,
                responded_at=responded_at,
            )

    @staticmethod
    async def _on_completed(event: RequestCompletedEvent) -> None:
        completed_at = event.occurred_at or datetime.now(timezone.utc)
        async with get_session() as session:
            await EscalationRepository(session).mark_completed(
                event.request_id,
                completed_at=completed_at,
            )

    @staticmethod
    def subscribe_to_event_bus() -> None:
        global _subscribed
        if _subscribed:
            return

        from events.event_bus import subscribe

        for event_type in (RequestAssignedEvent, ManagerFirstResponseEvent, RequestCompletedEvent):
            subscribe(
                event_type,
                SlaTimerService.handle_event,
                handler_id=f"sla_timer_{event_type.__name__}",
            )
        _subscribed = True
        logger.info("sla_timer_service_subscribed")

    @staticmethod
    def reset_subscription() -> None:
        global _subscribed
        _subscribed = False


def _log_task_error(task: asyncio.Task) -> None:
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        logger.warning("sla_timer background task failed: %s", exc, exc_info=exc)


sla_timer_service = SlaTimerService()
