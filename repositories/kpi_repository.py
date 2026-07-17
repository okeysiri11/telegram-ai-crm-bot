# KPI repository — aggregate rollups and lifecycle tracking via request_metrics.

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.manager_kpi import ManagerDailyKpi, ManagerMonthlyKpi, VerticalKpi
from database.models.platform_metrics import RequestMetric
from models.manager_kpi import KpiTotals, month_start
from src.platform.layers.base_repository import BaseRepository


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _seconds_between(start: datetime, end: datetime) -> int:
    return max(0, int((end - start).total_seconds()))


def _normalize_vertical(vertical: str | None) -> str:
    return (vertical or "unknown").strip().lower()


class KpiRepository(BaseRepository):
    async def get_request_metric(self, request_number: str) -> RequestMetric | None:
        result = await self.session.execute(
            select(RequestMetric).where(RequestMetric.request_number == request_number)
        )
        return result.scalar_one_or_none()

    async def ensure_request_metric(
        self,
        *,
        request_number: str,
        vertical: str,
        request_type: str,
        request_id: uuid.UUID | str | None = None,
        manager_id: uuid.UUID | str | None = None,
        client_telegram_id: int | None = None,
        created_at: datetime | None = None,
    ) -> RequestMetric:
        existing = await self.get_request_metric(request_number)
        if existing is not None:
            return existing
        now = created_at or _utcnow()
        rid = uuid.UUID(str(request_id)) if request_id else None
        mid = uuid.UUID(str(manager_id)) if manager_id else None
        row = RequestMetric(
            request_number=request_number,
            request_id=rid,
            vertical=_normalize_vertical(vertical),
            request_type=request_type,
            status="NEW",
            manager_id=mid,
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
        manager_id: uuid.UUID | str,
        assigned_at: datetime | None = None,
    ) -> tuple[RequestMetric | None, bool]:
        row = await self.get_request_metric(request_number)
        if row is None:
            return None, False
        now = assigned_at or _utcnow()
        newly_assigned = row.assigned_at is None
        row.manager_id = uuid.UUID(str(manager_id))
        row.status = "ASSIGNED"
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
        response_time_seconds: int | None = None,
    ) -> tuple[RequestMetric | None, bool]:
        row = await self.get_request_metric(request_number)
        if row is None:
            return None, False
        now = responded_at or _utcnow()
        newly_responded = row.first_response_at is None
        if newly_responded:
            row.first_response_at = now
            row.time_to_first_response_seconds = (
                response_time_seconds
                if response_time_seconds is not None
                else _seconds_between(row.request_created_at, now)
            )
            row.status = "IN_PROGRESS"
        await self.session.flush()
        return row, newly_responded

    async def mark_closed(
        self,
        request_number: str,
        *,
        closed_at: datetime | None = None,
        converted_to_deal: bool = False,
    ) -> tuple[RequestMetric | None, bool]:
        row = await self.get_request_metric(request_number)
        if row is None:
            return None, False
        now = closed_at or _utcnow()
        newly_closed = row.closed_at is None
        if newly_closed:
            row.closed_at = now
            row.time_to_close_seconds = _seconds_between(row.request_created_at, now)
            row.status = "COMPLETED"
        row.converted_to_deal = converted_to_deal or row.converted_to_deal
        await self.session.flush()
        return row, newly_closed

    async def _get_or_create_manager_daily(
        self,
        *,
        manager_id: uuid.UUID,
        metric_date: date,
        vertical: str,
    ) -> ManagerDailyKpi:
        result = await self.session.execute(
            select(ManagerDailyKpi).where(
                ManagerDailyKpi.manager_id == manager_id,
                ManagerDailyKpi.metric_date == metric_date,
                ManagerDailyKpi.vertical == vertical,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = ManagerDailyKpi(
                manager_id=manager_id,
                metric_date=metric_date,
                vertical=vertical,
            )
            self.session.add(row)
            await self.session.flush()
        return row

    async def _get_or_create_manager_monthly(
        self,
        *,
        manager_id: uuid.UUID,
        metric_month: date,
        vertical: str,
    ) -> ManagerMonthlyKpi:
        result = await self.session.execute(
            select(ManagerMonthlyKpi).where(
                ManagerMonthlyKpi.manager_id == manager_id,
                ManagerMonthlyKpi.metric_month == metric_month,
                ManagerMonthlyKpi.vertical == vertical,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = ManagerMonthlyKpi(
                manager_id=manager_id,
                metric_month=metric_month,
                vertical=vertical,
            )
            self.session.add(row)
            await self.session.flush()
        return row

    async def _get_or_create_vertical(self, *, vertical: str, metric_date: date) -> VerticalKpi:
        vid = _normalize_vertical(vertical)
        result = await self.session.execute(
            select(VerticalKpi).where(
                VerticalKpi.vertical == vid,
                VerticalKpi.metric_date == metric_date,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = VerticalKpi(vertical=vid, metric_date=metric_date)
            self.session.add(row)
            await self.session.flush()
        return row

    async def bump_manager(
        self,
        *,
        manager_id: uuid.UUID | str,
        vertical: str,
        metric_date: date,
        assigned: int = 0,
        first_response: int = 0,
        completed: int = 0,
        converted: int = 0,
        overdue: int = 0,
        sla_compliant: int = 0,
        sla_total: int = 0,
        first_response_seconds: int = 0,
        response_seconds: int = 0,
        resolution_seconds: int = 0,
    ) -> None:
        mid = uuid.UUID(str(manager_id))
        vid = _normalize_vertical(vertical)
        month = month_start(metric_date)

        for bucket_vertical in (vid, "all"):
            daily = await self._get_or_create_manager_daily(
                manager_id=mid,
                metric_date=metric_date,
                vertical=bucket_vertical,
            )
            daily.requests_assigned += assigned
            daily.requests_first_response += first_response
            daily.requests_completed += completed
            daily.requests_converted += converted
            daily.requests_overdue += overdue
            daily.sla_compliant_count += sla_compliant
            daily.sla_total_count += sla_total
            daily.total_first_response_seconds += first_response_seconds
            daily.total_response_seconds += response_seconds or first_response_seconds
            daily.total_resolution_seconds += resolution_seconds

            monthly = await self._get_or_create_manager_monthly(
                manager_id=mid,
                metric_month=month,
                vertical=bucket_vertical,
            )
            monthly.requests_assigned += assigned
            monthly.requests_first_response += first_response
            monthly.requests_completed += completed
            monthly.requests_converted += converted
            monthly.requests_overdue += overdue
            monthly.sla_compliant_count += sla_compliant
            monthly.sla_total_count += sla_total
            monthly.total_first_response_seconds += first_response_seconds
            monthly.total_response_seconds += response_seconds or first_response_seconds
            monthly.total_resolution_seconds += resolution_seconds

        await self.session.flush()

    async def bump_vertical(
        self,
        *,
        vertical: str,
        metric_date: date,
        created: int = 0,
        assigned: int = 0,
        completed: int = 0,
        converted: int = 0,
        overdue: int = 0,
        sla_compliant: int = 0,
        sla_total: int = 0,
        first_response_seconds: int = 0,
        response_count: int = 0,
        resolution_seconds: int = 0,
    ) -> None:
        row = await self._get_or_create_vertical(vertical=vertical, metric_date=metric_date)
        row.requests_created += created
        row.requests_assigned += assigned
        row.requests_completed += completed
        row.requests_converted += converted
        row.requests_overdue += overdue
        row.sla_compliant_count += sla_compliant
        row.sla_total_count += sla_total
        row.total_first_response_seconds += first_response_seconds
        row.response_count += response_count
        row.total_resolution_seconds += resolution_seconds
        await self.session.flush()

    @staticmethod
    def _sum_manager_daily(rows: list[ManagerDailyKpi]) -> KpiTotals:
        totals = KpiTotals()
        for row in rows:
            totals.requests_assigned += row.requests_assigned
            totals.requests_first_response += row.requests_first_response
            totals.requests_completed += row.requests_completed
            totals.requests_converted += row.requests_converted
            totals.requests_overdue += row.requests_overdue
            totals.sla_compliant_count += row.sla_compliant_count
            totals.sla_total_count += row.sla_total_count
            totals.total_first_response_seconds += row.total_first_response_seconds
            totals.total_response_seconds += row.total_response_seconds
            totals.total_resolution_seconds += row.total_resolution_seconds
            totals.response_count += row.requests_first_response
        return totals

    @staticmethod
    def _sum_vertical(rows: list[VerticalKpi]) -> KpiTotals:
        totals = KpiTotals()
        for row in rows:
            totals.requests_created += row.requests_created
            totals.requests_assigned += row.requests_assigned
            totals.requests_completed += row.requests_completed
            totals.requests_converted += row.requests_converted
            totals.requests_overdue += row.requests_overdue
            totals.sla_compliant_count += row.sla_compliant_count
            totals.sla_total_count += row.sla_total_count
            totals.total_first_response_seconds += row.total_first_response_seconds
            totals.total_response_seconds += row.total_first_response_seconds
            totals.total_resolution_seconds += row.total_resolution_seconds
            totals.response_count += row.response_count
        return totals

    async def aggregate_manager_kpi(
        self,
        manager_id: uuid.UUID | str,
        *,
        start_date: date | None,
        end_date: date,
    ) -> tuple[KpiTotals, dict[str, dict[str, Any]]]:
        mid = uuid.UUID(str(manager_id))
        query = select(ManagerDailyKpi).where(
            ManagerDailyKpi.manager_id == mid,
            ManagerDailyKpi.vertical != "all",
        )
        if start_date is not None:
            query = query.where(
                ManagerDailyKpi.metric_date >= start_date,
                ManagerDailyKpi.metric_date <= end_date,
            )
        result = await self.session.execute(query)
        rows = list(result.scalars().all())

        by_vertical: dict[str, KpiTotals] = {}
        for row in rows:
            bucket = by_vertical.setdefault(row.vertical, KpiTotals())
            bucket.requests_assigned += row.requests_assigned
            bucket.requests_first_response += row.requests_first_response
            bucket.requests_completed += row.requests_completed
            bucket.requests_converted += row.requests_converted
            bucket.requests_overdue += row.requests_overdue
            bucket.sla_compliant_count += row.sla_compliant_count
            bucket.sla_total_count += row.sla_total_count
            bucket.total_first_response_seconds += row.total_first_response_seconds
            bucket.total_response_seconds += row.total_response_seconds
            bucket.total_resolution_seconds += row.total_resolution_seconds
            bucket.response_count += row.requests_first_response

        totals = KpiTotals()
        for bucket in by_vertical.values():
            totals.requests_assigned += bucket.requests_assigned
            totals.requests_first_response += bucket.requests_first_response
            totals.requests_completed += bucket.requests_completed
            totals.requests_converted += bucket.requests_converted
            totals.requests_overdue += bucket.requests_overdue
            totals.sla_compliant_count += bucket.sla_compliant_count
            totals.sla_total_count += bucket.sla_total_count
            totals.total_first_response_seconds += bucket.total_first_response_seconds
            totals.total_response_seconds += bucket.total_response_seconds
            totals.total_resolution_seconds += bucket.total_resolution_seconds
            totals.response_count += bucket.response_count

        return totals, {v: t.to_metrics_dict() for v, t in by_vertical.items()}

    async def aggregate_vertical_kpi(
        self,
        vertical: str,
        *,
        start_date: date | None,
        end_date: date,
    ) -> KpiTotals:
        vid = _normalize_vertical(vertical)
        query = select(VerticalKpi).where(VerticalKpi.vertical == vid)
        if start_date is not None:
            query = query.where(
                VerticalKpi.metric_date >= start_date,
                VerticalKpi.metric_date <= end_date,
            )
        result = await self.session.execute(query)
        return self._sum_vertical(list(result.scalars().all()))

    async def aggregate_platform_kpi(
        self,
        *,
        start_date: date | None,
        end_date: date,
    ) -> tuple[KpiTotals, dict[str, dict[str, Any]]]:
        query = select(VerticalKpi)
        if start_date is not None:
            query = query.where(
                VerticalKpi.metric_date >= start_date,
                VerticalKpi.metric_date <= end_date,
            )
        result = await self.session.execute(query)
        rows = list(result.scalars().all())

        by_vertical: dict[str, KpiTotals] = {}
        for row in rows:
            bucket = by_vertical.setdefault(row.vertical, KpiTotals())
            bucket.requests_created += row.requests_created
            bucket.requests_assigned += row.requests_assigned
            bucket.requests_completed += row.requests_completed
            bucket.requests_converted += row.requests_converted
            bucket.requests_overdue += row.requests_overdue
            bucket.sla_compliant_count += row.sla_compliant_count
            bucket.sla_total_count += row.sla_total_count
            bucket.total_first_response_seconds += row.total_first_response_seconds
            bucket.total_response_seconds += row.total_first_response_seconds
            bucket.total_resolution_seconds += row.total_resolution_seconds
            bucket.response_count += row.response_count

        totals = KpiTotals()
        for bucket in by_vertical.values():
            totals.requests_created += bucket.requests_created
            totals.requests_assigned += bucket.requests_assigned
            totals.requests_completed += bucket.requests_completed
            totals.requests_converted += bucket.requests_converted
            totals.requests_overdue += bucket.requests_overdue
            totals.sla_compliant_count += bucket.sla_compliant_count
            totals.sla_total_count += bucket.sla_total_count
            totals.total_first_response_seconds += bucket.total_first_response_seconds
            totals.total_response_seconds += bucket.total_response_seconds
            totals.total_resolution_seconds += bucket.total_resolution_seconds
            totals.response_count += bucket.response_count

        return totals, {v: t.to_metrics_dict() for v, t in by_vertical.items()}

    async def manager_rankings(
        self,
        *,
        start_date: date | None,
        end_date: date,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        query = (
            select(
                ManagerDailyKpi.manager_id,
                func.sum(ManagerDailyKpi.requests_completed).label("completed"),
                func.sum(ManagerDailyKpi.requests_converted).label("converted"),
                func.sum(ManagerDailyKpi.sla_compliant_count).label("sla_ok"),
                func.sum(ManagerDailyKpi.sla_total_count).label("sla_total"),
                func.sum(ManagerDailyKpi.total_first_response_seconds).label("fr_secs"),
                func.sum(ManagerDailyKpi.requests_first_response).label("fr_count"),
            )
            .where(ManagerDailyKpi.vertical == "all")
            .group_by(ManagerDailyKpi.manager_id)
        )
        if start_date is not None:
            query = query.where(
                ManagerDailyKpi.metric_date >= start_date,
                ManagerDailyKpi.metric_date <= end_date,
            )

        result = await self.session.execute(query)
        rankings: list[dict[str, Any]] = []
        for row in result.all():
            completed = int(row.completed or 0)
            converted = int(row.converted or 0)
            sla_ok = int(row.sla_ok or 0)
            sla_total = int(row.sla_total or 0)
            fr_count = int(row.fr_count or 0)
            fr_secs = int(row.fr_secs or 0)
            sla_pct = round(100.0 * sla_ok / sla_total, 2) if sla_total else 0.0
            avg_fr = fr_secs / fr_count if fr_count else None
            conversion = round(converted / completed, 4) if completed else 0.0
            score = completed * 10 + converted * 25 + sla_ok * 5 - (fr_secs / 3600 if fr_secs else 0)
            rankings.append(
                {
                    "manager_id": str(row.manager_id),
                    "score": round(score, 2),
                    "requests_completed": completed,
                    "conversion_rate": conversion,
                    "sla_compliance_percent": sla_pct,
                    "first_response_time_seconds": avg_fr,
                }
            )

        rankings.sort(key=lambda item: item["score"], reverse=True)
        for idx, item in enumerate(rankings[:limit], start=1):
            item["rank"] = idx
        return rankings[:limit]
