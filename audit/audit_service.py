# AuditService — append-only audit trail subscribed to platform EventBus.

from __future__ import annotations

import asyncio
import logging
from typing import Any

from audit.audit_event import AuditRecord, audit_record_from_event
from audit.audit_repository import AuditRepository
from database.session import get_session
from events.base_event import BaseEvent
from events.owner_events import OwnerEscalationEvent
from events.configuration_events import ConfigurationChangedEvent
from events.request_events import (
    ManagerEscalationEvent,
    ManagerReassignedEvent,
    RequestAssignedEvent,
    RequestCompletedEvent,
    RequestCreatedEvent,
    RequestOverdueEvent,
)

logger = logging.getLogger(__name__)

_subscribed = False


class AuditService:
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
                logger.warning("audit_service sync fallback failed", exc_info=True)

    @staticmethod
    async def record(record: AuditRecord) -> dict[str, Any] | None:
        try:
            async with get_session() as session:
                row = await AuditRepository(session).insert(record)
                return AuditRepository.snapshot(row)
        except Exception:
            logger.warning(
                "audit_record_failed",
                extra={
                    "event_type": record.event_type,
                    "entity_id": record.entity_id,
                },
                exc_info=True,
            )
            return None

    @staticmethod
    async def _record_from_event(event: BaseEvent) -> None:
        record = audit_record_from_event(event)
        if record is None:
            return
        await AuditService.record(record)

    @staticmethod
    async def handle_event(event: BaseEvent) -> None:
        """EventBus handler — non-blocking, errors never propagate."""
        AuditService._enqueue(AuditService._record_from_event(event))

    @staticmethod
    async def get_request_history(
        *,
        request_id: str | None = None,
        request_number: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        async with get_session() as session:
            repo = AuditRepository(session)
            if request_id:
                rows = await repo.list_by_request_id(request_id, limit=limit)
            elif request_number:
                rows = await repo.list_by_request_number(request_number, limit=limit)
            else:
                return []
        return [AuditRepository.snapshot(row) for row in rows]

    @staticmethod
    async def get_manager_history(
        manager_id: str,
        *,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        async with get_session() as session:
            rows = await AuditRepository(session).list_by_manager_id(manager_id, limit=limit)
        return [AuditRepository.snapshot(row) for row in rows]

    @staticmethod
    def subscribe_to_event_bus() -> None:
        global _subscribed
        if _subscribed:
            return

        from events.event_bus import subscribe

        event_types = (
            RequestCreatedEvent,
            RequestAssignedEvent,
            RequestCompletedEvent,
            ManagerReassignedEvent,
            RequestOverdueEvent,
            ManagerEscalationEvent,
            OwnerEscalationEvent,
            ConfigurationChangedEvent,
        )
        for event_type in event_types:
            subscribe(
                event_type,
                AuditService.handle_event,
                handler_id=f"audit_trail_{event_type.__name__}",
            )
        _subscribed = True
        logger.info(
            "audit_service_subscribed",
            extra={"event_types": [et.__name__ for et in event_types]},
        )

    @staticmethod
    def reset_subscription() -> None:
        global _subscribed
        _subscribed = False


def _log_task_error(task: asyncio.Task) -> None:
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        logger.warning("audit_service background task failed: %s", exc, exc_info=exc)


audit_service = AuditService()
