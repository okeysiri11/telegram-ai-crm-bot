# Platform metrics repository — SQL only.

from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.platform_metrics import (
    ManagerMetric,
    PlatformMetricsDaily,
    RequestMetric,
)
from src.platform.layers.base_repository import BaseRepository


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _seconds_between(start: datetime, end: datetime) -> int:
    return max(0, int((end - start).total_seconds()))


class PlatformMetricsRepository(BaseRepository):
    async def get_request_metric(self, request_number: str) -> RequestMetric | None:
        result = await self.session.execute(
            select(RequestMetric).where(RequestMetric.request_number == request_number)
        )
        return result.scalar_one_or_none()

    async def insert_request_metric(
        self,
        *,
        request_number: str,
        request_id: uuid.UUID | None,
        vertical: str,
        request_type: str,
        status: str,
        manager_id: uuid.UUID | None,
        client_telegram_id: int | None,
        request_created_at: datetime | None = None,
    ) -> RequestMetric:
        now = request_created_at or _utcnow()
        row = RequestMetric(
            request_number=request_number,
            request_id=request_id,
            vertical=vertical,
            request_type=request_type,
            status=status,
            manager_id=manager_id,
            client_telegram_id=client_telegram_id,
            request_created_at=now,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def mark_assigned(
        self,
        request_number: str,
        *,
        manager_id: uuid.UUID,
        assigned_at: datetime | None = None,
        status: str = "ASSIGNED",
    ) -> tuple[RequestMetric | None, bool]:
        row = await self.get_request_metric(request_number)
        if row is None:
            return None, False
        now = assigned_at or _utcnow()
        newly_assigned = row.assigned_at is None
        row.manager_id = manager_id
        row.status = status
        if newly_assigned:
            row.assigned_at = now
            row.time_to_assign_seconds = _seconds_between(row.request_created_at, now)
        await self.session.flush()
        return row, newly_assigned

    async def mark_first_response(
        self,
        request_number: str,
        *,
        responded_at: datetime | None = None,
        status: str = "IN_PROGRESS",
    ) -> tuple[RequestMetric | None, bool]:
        row = await self.get_request_metric(request_number)
        if row is None:
            return None, False
        now = responded_at or _utcnow()
        row.status = status
        newly_responded = row.first_response_at is None
        if newly_responded:
            row.first_response_at = now
            row.time_to_first_response_seconds = _seconds_between(row.request_created_at, now)
        await self.session.flush()
        return row, newly_responded

    async def mark_closed(
        self,
        request_number: str,
        *,
        closed_at: datetime | None = None,
        status: str = "COMPLETED",
        converted_to_deal: bool = False,
    ) -> tuple[RequestMetric | None, bool]:
        row = await self.get_request_metric(request_number)
        if row is None:
            return None, False
        now = closed_at or _utcnow()
        newly_closed = row.closed_at is None
        row.status = status
        if newly_closed:
            row.closed_at = now
            row.time_to_close_seconds = _seconds_between(row.request_created_at, now)
        row.converted_to_deal = converted_to_deal or row.converted_to_deal
        await self.session.flush()
        return row, newly_closed

    async def bump_manager_daily(
        self,
        *,
        manager_id: uuid.UUID,
        vertical: str,
        metric_date: date,
        assigned: int = 0,
        responded: int = 0,
        closed: int = 0,
        deal: int = 0,
        response_seconds: int = 0,
    ) -> ManagerMetric:
        result = await self.session.execute(
            select(ManagerMetric).where(
                ManagerMetric.manager_id == manager_id,
                ManagerMetric.metric_date == metric_date,
                ManagerMetric.vertical == vertical,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = ManagerMetric(
                manager_id=manager_id,
                metric_date=metric_date,
                vertical=vertical,
            )
            self.session.add(row)
            await self.session.flush()

        row.requests_assigned += assigned
        row.requests_with_response += responded
        row.requests_closed += closed
        row.deals_won += deal
        row.total_response_time_seconds += response_seconds
        await self.session.flush()
        return row

    async def bump_platform_daily(
        self,
        *,
        vertical: str,
        metric_date: date,
        created: int = 0,
        assigned: int = 0,
        closed: int = 0,
        deal: int = 0,
        response_seconds: int = 0,
        response_count: int = 0,
        request_type: str | None = None,
    ) -> PlatformMetricsDaily:
        result = await self.session.execute(
            select(PlatformMetricsDaily).where(
                PlatformMetricsDaily.metric_date == metric_date,
                PlatformMetricsDaily.vertical == vertical,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = PlatformMetricsDaily(metric_date=metric_date, vertical=vertical)
            self.session.add(row)
            await self.session.flush()

        row.requests_created += created
        row.requests_assigned += assigned
        row.requests_closed += closed
        row.requests_deal += deal
        row.total_response_time_seconds += response_seconds
        row.response_count += response_count

        if request_type and created:
            counts: dict[str, int] = {}
            if row.requests_by_type:
                try:
                    counts = json.loads(row.requests_by_type)
                except json.JSONDecodeError:
                    counts = {}
            counts[request_type] = counts.get(request_type, 0) + created
            row.requests_by_type = json.dumps(counts, ensure_ascii=False)

        await self.session.flush()
        return row

    async def average_response_time(
        self,
        *,
        vertical: str | None = None,
        days: int = 30,
    ) -> float | None:
        cutoff = _utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        q = select(func.avg(RequestMetric.time_to_first_response_seconds)).where(
            RequestMetric.first_response_at.is_not(None),
            RequestMetric.request_created_at >= cutoff,
        )
        if vertical:
            q = q.where(RequestMetric.vertical == vertical)
        result = await self.session.execute(q)
        val = result.scalar_one_or_none()
        return float(val) if val is not None else None

    async def requests_per_day(self, *, days: int = 30) -> list[dict[str, Any]]:
        q = (
            select(
                func.date(RequestMetric.request_created_at).label("day"),
                func.count().label("count"),
            )
            .group_by(func.date(RequestMetric.request_created_at))
            .order_by(func.date(RequestMetric.request_created_at).desc())
            .limit(days)
        )
        result = await self.session.execute(q)
        return [{"date": str(row.day), "count": int(row.count)} for row in result.all()]

    async def requests_per_vertical(self, *, days: int = 30) -> list[dict[str, Any]]:
        q = (
            select(
                RequestMetric.vertical,
                func.count().label("count"),
            )
            .group_by(RequestMetric.vertical)
            .order_by(func.count().desc())
        )
        result = await self.session.execute(q)
        return [{"vertical": row.vertical, "count": int(row.count)} for row in result.all()]

    async def conversion_to_deal(self, *, vertical: str | None = None, days: int = 30) -> float | None:
        q_created = select(func.count()).select_from(RequestMetric)
        q_deal = select(func.count()).select_from(RequestMetric).where(
            RequestMetric.converted_to_deal.is_(True)
        )
        if vertical:
            q_created = q_created.where(RequestMetric.vertical == vertical)
            q_deal = q_deal.where(RequestMetric.vertical == vertical)

        created = int((await self.session.execute(q_created)).scalar_one())
        deals = int((await self.session.execute(q_deal)).scalar_one())
        if created <= 0:
            return None
        return deals / created
