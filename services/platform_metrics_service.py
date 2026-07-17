# PlatformMetricsService — async observability for requests, managers, verticals.

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from database.session import get_session
from repositories.platform_metrics_repository import PlatformMetricsRepository

logger = logging.getLogger(__name__)

_DEAL_STATUSES = frozenset({"DEAL", "COMPLETED", "CLOSED"})
_CLOSED_STATUSES = frozenset({"COMPLETED", "CANCELLED", "CLOSED", "DONE"})


def _infer_vertical(request_number: str, request_type: str, vertical: str | None = None) -> str:
    if vertical:
        return vertical.strip().lower()
    prefix = (request_number or "").split("-", 1)[0].lower()
    mapping = {
        "auto": "auto",
        "agro": "agro",
        "realty": "realty",
        "legal": "legal",
        "logistics": "logistics",
    }
    if prefix in mapping:
        return mapping[prefix]
    rt = (request_type or "").lower()
    for key in ("auto", "agro", "realty", "legal", "logistics"):
        if key in rt:
            return key
    return "unknown"


class PlatformMetricsService:
    """Fire-and-forget metrics — never blocks Telegram handlers."""

    @staticmethod
    def _enqueue(coro) -> None:
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(coro)
            task.add_done_callback(_log_task_error)
        except RuntimeError:
            asyncio.run(coro)

    @staticmethod
    async def _write_request_created(
        *,
        request_number: str,
        request_type: str,
        status: str = "NEW",
        vertical: str | None = None,
        request_id: uuid.UUID | str | None = None,
        manager_id: uuid.UUID | str | None = None,
        client_telegram_id: int | None = None,
        request_created_at: datetime | None = None,
    ) -> None:
        vid = _infer_vertical(request_number, request_type, vertical)
        rid = uuid.UUID(str(request_id)) if request_id else None
        mid = uuid.UUID(str(manager_id)) if manager_id else None
        now = request_created_at or datetime.now(timezone.utc)

        async with get_session() as session:
            repo = PlatformMetricsRepository(session)
            existing = await repo.get_request_metric(request_number)
            if existing is not None:
                return
            await repo.insert_request_metric(
                request_number=request_number,
                request_id=rid,
                vertical=vid,
                request_type=request_type,
                status=status,
                manager_id=mid,
                client_telegram_id=client_telegram_id,
                request_created_at=now,
            )
            await repo.bump_platform_daily(
                vertical=vid,
                metric_date=now.date(),
                created=1,
                request_type=request_type,
            )
            if mid is not None:
                row, newly_assigned = await repo.mark_assigned(
                    request_number,
                    manager_id=mid,
                    assigned_at=now,
                    status="ASSIGNED",
                )
                if newly_assigned:
                    await repo.bump_platform_daily(
                        vertical=vid,
                        metric_date=now.date(),
                        assigned=1,
                    )
                    await repo.bump_manager_daily(
                        manager_id=mid,
                        vertical=vid,
                        metric_date=now.date(),
                        assigned=1,
                    )

    @staticmethod
    async def _write_manager_assigned(
        *,
        request_number: str,
        manager_id: uuid.UUID | str,
        status: str = "ASSIGNED",
        assigned_at: datetime | None = None,
    ) -> None:
        mid = uuid.UUID(str(manager_id))
        now = assigned_at or datetime.now(timezone.utc)

        async with get_session() as session:
            repo = PlatformMetricsRepository(session)
            row, newly_assigned = await repo.mark_assigned(
                request_number,
                manager_id=mid,
                assigned_at=now,
                status=status,
            )
            if row is None or not newly_assigned:
                return
            await repo.bump_platform_daily(
                vertical=row.vertical,
                metric_date=now.date(),
                assigned=1,
            )
            await repo.bump_manager_daily(
                manager_id=mid,
                vertical=row.vertical,
                metric_date=now.date(),
                assigned=1,
            )

    @staticmethod
    async def _write_manager_first_response(
        *,
        request_number: str,
        status: str = "IN_PROGRESS",
        responded_at: datetime | None = None,
        manager_id: uuid.UUID | str | None = None,
    ) -> None:
        now = responded_at or datetime.now(timezone.utc)

        async with get_session() as session:
            repo = PlatformMetricsRepository(session)
            row, newly_responded = await repo.mark_first_response(
                request_number,
                responded_at=now,
                status=status,
            )
            if row is None or not newly_responded:
                return
            mid = row.manager_id
            if manager_id is not None:
                mid = uuid.UUID(str(manager_id))
            response_secs = row.time_to_first_response_seconds or 0
            await repo.bump_platform_daily(
                vertical=row.vertical,
                metric_date=now.date(),
                response_seconds=response_secs,
                response_count=1,
            )
            if mid is not None:
                await repo.bump_manager_daily(
                    manager_id=mid,
                    vertical=row.vertical,
                    metric_date=now.date(),
                    responded=1,
                    response_seconds=response_secs,
                )

    @staticmethod
    async def _write_request_closed(
        *,
        request_number: str,
        status: str = "COMPLETED",
        closed_at: datetime | None = None,
        converted_to_deal: bool = False,
    ) -> None:
        now = closed_at or datetime.now(timezone.utc)
        is_deal = converted_to_deal or status.upper() in _DEAL_STATUSES

        async with get_session() as session:
            repo = PlatformMetricsRepository(session)
            row, newly_closed = await repo.mark_closed(
                request_number,
                closed_at=now,
                status=status,
                converted_to_deal=is_deal,
            )
            if row is None or not newly_closed:
                return
            await repo.bump_platform_daily(
                vertical=row.vertical,
                metric_date=now.date(),
                closed=1,
                deal=1 if is_deal else 0,
            )
            if row.manager_id is not None:
                await repo.bump_manager_daily(
                    manager_id=row.manager_id,
                    vertical=row.vertical,
                    metric_date=now.date(),
                    closed=1,
                    deal=1 if is_deal else 0,
                )

    @staticmethod
    async def track_request_created(
        *,
        request_number: str,
        request_type: str,
        status: str = "NEW",
        vertical: str | None = None,
        request_id: uuid.UUID | str | None = None,
        manager_id: uuid.UUID | str | None = None,
        client_telegram_id: int | None = None,
        request_created_at: datetime | None = None,
    ) -> None:
        PlatformMetricsService._enqueue(
            PlatformMetricsService._write_request_created(
                request_number=request_number,
                request_type=request_type,
                status=status,
                vertical=vertical,
                request_id=request_id,
                manager_id=manager_id,
                client_telegram_id=client_telegram_id,
                request_created_at=request_created_at,
            )
        )

    @staticmethod
    async def track_manager_assigned(
        *,
        request_number: str,
        manager_id: uuid.UUID | str,
        status: str = "ASSIGNED",
        assigned_at: datetime | None = None,
    ) -> None:
        PlatformMetricsService._enqueue(
            PlatformMetricsService._write_manager_assigned(
                request_number=request_number,
                manager_id=manager_id,
                status=status,
                assigned_at=assigned_at,
            )
        )

    @staticmethod
    async def track_manager_first_response(
        *,
        request_number: str,
        status: str = "IN_PROGRESS",
        responded_at: datetime | None = None,
        manager_id: uuid.UUID | str | None = None,
    ) -> None:
        PlatformMetricsService._enqueue(
            PlatformMetricsService._write_manager_first_response(
                request_number=request_number,
                status=status,
                responded_at=responded_at,
                manager_id=manager_id,
            )
        )

    @staticmethod
    async def track_request_closed(
        *,
        request_number: str,
        status: str = "COMPLETED",
        closed_at: datetime | None = None,
        converted_to_deal: bool = False,
    ) -> None:
        PlatformMetricsService._enqueue(
            PlatformMetricsService._write_request_closed(
                request_number=request_number,
                status=status,
                closed_at=closed_at,
                converted_to_deal=converted_to_deal,
            )
        )

    @staticmethod
    async def average_response_time(
        *,
        vertical: str | None = None,
        days: int = 30,
    ) -> float | None:
        async with get_session() as session:
            return await PlatformMetricsRepository(session).average_response_time(
                vertical=vertical,
                days=days,
            )

    @staticmethod
    async def requests_per_day(*, days: int = 30) -> list[dict[str, Any]]:
        async with get_session() as session:
            return await PlatformMetricsRepository(session).requests_per_day(days=days)

    @staticmethod
    async def requests_per_vertical(*, days: int = 30) -> list[dict[str, Any]]:
        async with get_session() as session:
            return await PlatformMetricsRepository(session).requests_per_vertical(days=days)

    @staticmethod
    async def conversion_to_deal(
        *,
        vertical: str | None = None,
        days: int = 30,
    ) -> float | None:
        async with get_session() as session:
            return await PlatformMetricsRepository(session).conversion_to_deal(
                vertical=vertical,
                days=days,
            )

    @staticmethod
    async def dashboard_summary(*, days: int = 30) -> dict[str, Any]:
        verticals = await PlatformMetricsService.requests_per_vertical(days=days)
        by_vertical: dict[str, Any] = {}
        for item in verticals:
            v = item["vertical"]
            by_vertical[v] = {
                "count": item["count"],
                "conversion_to_deal": await PlatformMetricsService.conversion_to_deal(
                    vertical=v,
                    days=days,
                ),
                "average_response_time_seconds": await PlatformMetricsService.average_response_time(
                    vertical=v,
                    days=days,
                ),
            }
        return {
            "average_response_time_seconds": await PlatformMetricsService.average_response_time(
                days=days
            ),
            "requests_per_day": await PlatformMetricsService.requests_per_day(days=days),
            "requests_per_vertical": verticals,
            "conversion_to_deal": await PlatformMetricsService.conversion_to_deal(days=days),
            "by_vertical": by_vertical,
        }


def _log_task_error(task: asyncio.Task) -> None:
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        logger.warning("platform_metrics background task failed: %s", exc, exc_info=exc)


platform_metrics_service = PlatformMetricsService()
