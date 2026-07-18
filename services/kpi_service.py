# KpiService — platform KPI engine with EventBus subscribers and cached reads.

from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from database.session import get_session
from events.base_event import BaseEvent
from events.owner_events import OwnerEscalationEvent
from events.request_events import (
    ManagerFirstResponseEvent,
    RequestAssignedEvent,
    RequestCompletedEvent,
    RequestCreatedEvent,
    RequestOverdueEvent,
)
from models.manager_kpi import (
    KpiPeriod,
    ManagerKpiSnapshot,
    PlatformKpiSnapshot,
    VerticalKpiSnapshot,
    period_bounds,
)
from repositories.kpi_repository import KpiRepository

logger = logging.getLogger(__name__)

_CACHE_TTL_SECONDS = 300
_subscribed = False
_cache: dict[str, tuple[float, dict[str, Any]]] = {}

SLA_FIRST_RESPONSE_SEC = int(os.getenv("SLA_FIRST_RESPONSE_SEC", str(30 * 60)))


class KpiService:
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
                logger.warning("kpi_service sync fallback failed", exc_info=True)

    @staticmethod
    def _cache_get(key: str) -> dict[str, Any] | None:
        entry = _cache.get(key)
        if entry is None:
            return None
        ts, payload = entry
        if time.monotonic() - ts > _CACHE_TTL_SECONDS:
            _cache.pop(key, None)
            return None
        return payload

    @staticmethod
    def _cache_set(key: str, payload: dict[str, Any]) -> None:
        _cache[key] = (time.monotonic(), payload)

    @staticmethod
    def invalidate_cache() -> None:
        _cache.clear()

    @staticmethod
    async def handle_event(event: BaseEvent) -> None:
        KpiService._enqueue(KpiService._process_event(event))

    @staticmethod
    async def _process_event(event: BaseEvent) -> None:
        try:
            if isinstance(event, RequestCreatedEvent):
                await KpiService._on_request_created(event)
            elif isinstance(event, RequestAssignedEvent):
                await KpiService._on_request_assigned(event)
            elif isinstance(event, ManagerFirstResponseEvent):
                await KpiService._on_manager_first_response(event)
            elif isinstance(event, RequestCompletedEvent):
                await KpiService._on_request_completed(event)
            elif isinstance(event, RequestOverdueEvent):
                await KpiService._on_request_overdue(event)
            elif isinstance(event, OwnerEscalationEvent):
                await KpiService._on_owner_escalation(event)
        except Exception:
            logger.warning(
                "kpi_event_processing_failed",
                extra={"event_type": event.event_type, "event_id": event.event_id},
                exc_info=True,
            )

    @staticmethod
    async def _on_request_created(event: RequestCreatedEvent) -> None:
        now = event.occurred_at or datetime.now(timezone.utc)
        async with get_session() as session:
            repo = KpiRepository(session)
            await repo.ensure_request_metric(
                request_number=event.request_number,
                vertical=event.vertical,
                request_type=event.request_type,
                request_id=event.request_id,
                manager_id=event.manager_id,
                client_telegram_id=event.client_telegram_id,
                created_at=now,
            )
            await repo.bump_vertical(
                vertical=event.vertical,
                metric_date=now.date(),
                created=1,
            )
            if event.manager_id:
                _, newly_assigned = await repo.mark_assigned(
                    event.request_number,
                    manager_id=event.manager_id,
                    assigned_at=now,
                )
                if newly_assigned:
                    await repo.bump_vertical(
                        vertical=event.vertical,
                        metric_date=now.date(),
                        assigned=1,
                    )
                    await repo.bump_manager(
                        manager_id=event.manager_id,
                        vertical=event.vertical,
                        metric_date=now.date(),
                        assigned=1,
                    )
        KpiService.invalidate_cache()

    @staticmethod
    async def _on_request_assigned(event: RequestAssignedEvent) -> None:
        now = event.occurred_at or datetime.now(timezone.utc)
        async with get_session() as session:
            repo = KpiRepository(session)
            _, newly_assigned = await repo.mark_assigned(
                event.request_number,
                manager_id=event.manager_id,
                assigned_at=now,
            )
            if not newly_assigned:
                return
            await repo.bump_vertical(
                vertical=event.vertical,
                metric_date=now.date(),
                assigned=1,
            )
            await repo.bump_manager(
                manager_id=event.manager_id,
                vertical=event.vertical,
                metric_date=now.date(),
                assigned=1,
            )
        KpiService.invalidate_cache()

    @staticmethod
    async def _on_manager_first_response(event: ManagerFirstResponseEvent) -> None:
        now = event.occurred_at or datetime.now(timezone.utc)
        response_secs = event.response_time_seconds
        sla_compliant = 1 if event.sla_compliant else 0
        sla_total = 1

        async with get_session() as session:
            repo = KpiRepository(session)
            row, newly_responded = await repo.mark_first_response(
                event.request_number,
                responded_at=now,
                response_time_seconds=response_secs or None,
            )
            if not newly_responded:
                return
            secs = response_secs or (row.time_to_first_response_seconds if row else 0) or 0
            if event.sla_compliant is False:
                sla_compliant = 0
            elif row and row.time_to_first_response_seconds is not None:
                sla_compliant = 1 if row.time_to_first_response_seconds <= SLA_FIRST_RESPONSE_SEC else 0

            await repo.bump_vertical(
                vertical=event.vertical,
                metric_date=now.date(),
                first_response_seconds=secs,
                response_count=1,
                sla_compliant=sla_compliant,
                sla_total=sla_total,
            )
            await repo.bump_manager(
                manager_id=event.manager_id,
                vertical=event.vertical,
                metric_date=now.date(),
                first_response=1,
                first_response_seconds=secs,
                response_seconds=secs,
                sla_compliant=sla_compliant,
                sla_total=sla_total,
            )
        KpiService.invalidate_cache()

    @staticmethod
    async def _on_request_completed(event: RequestCompletedEvent) -> None:
        now = event.occurred_at or datetime.now(timezone.utc)
        converted = event.converted_to_deal

        async with get_session() as session:
            repo = KpiRepository(session)
            row, newly_closed = await repo.mark_closed(
                event.request_number,
                closed_at=now,
                converted_to_deal=converted,
            )
            if not newly_closed:
                return
            resolution_secs = row.time_to_close_seconds if row else 0
            await repo.bump_vertical(
                vertical=event.vertical,
                metric_date=now.date(),
                completed=1,
                converted=1 if converted else 0,
                resolution_seconds=resolution_secs or 0,
            )
            if event.manager_id:
                await repo.bump_manager(
                    manager_id=event.manager_id,
                    vertical=event.vertical,
                    metric_date=now.date(),
                    completed=1,
                    converted=1 if converted else 0,
                    resolution_seconds=resolution_secs or 0,
                )
        KpiService.invalidate_cache()

    @staticmethod
    async def _on_request_overdue(event: RequestOverdueEvent) -> None:
        now = event.occurred_at or datetime.now(timezone.utc)
        async with get_session() as session:
            repo = KpiRepository(session)
            await repo.ensure_request_metric(
                request_number=event.request_number,
                vertical=event.vertical,
                request_type=event.request_type,
                request_id=event.request_id,
                manager_id=event.manager_id,
            )
            await repo.bump_vertical(
                vertical=event.vertical,
                metric_date=now.date(),
                overdue=1,
                sla_total=1,
            )
            if event.manager_id:
                await repo.bump_manager(
                    manager_id=event.manager_id,
                    vertical=event.vertical,
                    metric_date=now.date(),
                    overdue=1,
                    sla_total=1,
                )
        KpiService.invalidate_cache()

    @staticmethod
    async def _on_owner_escalation(event: OwnerEscalationEvent) -> None:
        now = event.occurred_at or datetime.now(timezone.utc)
        async with get_session() as session:
            repo = KpiRepository(session)
            await repo.bump_vertical(
                vertical="__owner_escalations__",
                metric_date=now.date(),
                overdue=1,
            )
            await repo.bump_vertical(
                vertical=event.vertical,
                metric_date=now.date(),
                overdue=1,
                sla_total=1,
            )
        KpiService.invalidate_cache()

    @staticmethod
    async def get_manager_kpi(
        manager_id: uuid.UUID | str,
        *,
        period: KpiPeriod = "month",
    ) -> dict[str, Any]:
        cache_key = f"manager:{manager_id}:{period}"
        cached = KpiService._cache_get(cache_key)
        if cached is not None:
            return cached

        start_date, end_date = period_bounds(period)
        async with get_session() as session:
            totals, by_vertical = await KpiRepository(session).aggregate_manager_kpi(
                manager_id,
                start_date=start_date,
                end_date=end_date,
            )

        snapshot = ManagerKpiSnapshot(
            manager_id=str(manager_id),
            period=period,
            totals=totals,
            by_vertical=by_vertical,
        )
        payload = snapshot.to_dict()
        KpiService._cache_set(cache_key, payload)
        return payload

    @staticmethod
    async def get_vertical_kpi(
        vertical: str,
        *,
        period: KpiPeriod = "month",
    ) -> dict[str, Any]:
        cache_key = f"vertical:{vertical.lower()}:{period}"
        cached = KpiService._cache_get(cache_key)
        if cached is not None:
            return cached

        start_date, end_date = period_bounds(period)
        async with get_session() as session:
            totals = await KpiRepository(session).aggregate_vertical_kpi(
                vertical,
                start_date=start_date,
                end_date=end_date,
            )

        snapshot = VerticalKpiSnapshot(
            vertical=vertical,
            period=period,
            totals=totals,
        )
        payload = snapshot.to_dict()
        KpiService._cache_set(cache_key, payload)
        return payload

    @staticmethod
    async def get_platform_kpi(*, period: KpiPeriod = "month") -> dict[str, Any]:
        cache_key = f"platform:{period}"
        cached = KpiService._cache_get(cache_key)
        if cached is not None:
            return cached

        start_date, end_date = period_bounds(period)
        async with get_session() as session:
            repo = KpiRepository(session)
            totals, by_vertical = await repo.aggregate_platform_kpi(
                start_date=start_date,
                end_date=end_date,
            )
            rankings = await repo.manager_rankings(
                start_date=start_date,
                end_date=end_date,
            )

        snapshot = PlatformKpiSnapshot(
            period=period,
            totals=totals,
            by_vertical=by_vertical,
            manager_rankings=rankings,
        )
        payload = snapshot.to_dict()
        from services.owner_escalation_service import owner_escalation_service

        payload["owner_escalations"] = await owner_escalation_service.get_owner_escalation_kpi()
        KpiService._cache_set(cache_key, payload)
        return payload

    @staticmethod
    def subscribe_to_event_bus() -> None:
        global _subscribed
        if _subscribed:
            return

        from events.event_bus import subscribe

        event_types = (
            RequestCreatedEvent,
            RequestAssignedEvent,
            ManagerFirstResponseEvent,
            RequestCompletedEvent,
            RequestOverdueEvent,
            OwnerEscalationEvent,
        )
        for event_type in event_types:
            subscribe(
                event_type,
                KpiService.handle_event,
                handler_id=f"kpi_{event_type.__name__}",
            )
        _subscribed = True
        logger.info(
            "kpi_service_subscribed",
            extra={"event_types": [et.__name__ for et in event_types]},
        )

    @staticmethod
    def reset_subscription() -> None:
        global _subscribed
        _subscribed = False
        KpiService.invalidate_cache()


def _log_task_error(task: asyncio.Task) -> None:
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        logger.warning("kpi_service background task failed: %s", exc, exc_info=exc)


kpi_service = KpiService()
