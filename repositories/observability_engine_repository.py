# Observability Engine v1 repositories.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.observability_engine import (
    BusinessMetric,
    ErrorEvent,
    ErrorSeverity,
    PerformanceMetric,
    SystemMetric,
)


class SystemMetricRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        metric_name: str,
        metric_value: Decimal | float | int,
        unit: str = "count",
        tags: dict | None = None,
        recorded_at: datetime | None = None,
        **extra: Any,
    ) -> SystemMetric:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        row = SystemMetric(
            metric_name=metric_name,
            metric_value=Decimal(str(metric_value)),
            unit=unit,
            tags=tags,
            recorded_at=recorded_at or datetime.now(timezone.utc),
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_recent(
        self,
        *,
        metric_name: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[SystemMetric]:
        query = select(SystemMetric)
        if metric_name is not None:
            query = query.where(SystemMetric.metric_name == metric_name)
        if since is not None:
            query = query.where(SystemMetric.recorded_at >= since)
        result = await self._session.execute(
            query.order_by(SystemMetric.recorded_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def aggregate(
        self,
        *,
        metric_name: str,
        since: datetime,
    ) -> dict[str, Any]:
        result = await self._session.execute(
            select(
                func.count(SystemMetric.id),
                func.avg(SystemMetric.metric_value),
                func.max(SystemMetric.metric_value),
                func.min(SystemMetric.metric_value),
            ).where(
                SystemMetric.metric_name == metric_name,
                SystemMetric.recorded_at >= since,
            )
        )
        count, avg_val, max_val, min_val = result.one()
        return {
            "count": count or 0,
            "avg": float(avg_val) if avg_val is not None else 0.0,
            "max": float(max_val) if max_val is not None else 0.0,
            "min": float(min_val) if min_val is not None else 0.0,
        }


class BusinessMetricRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        kpi_name: str,
        kpi_value: Decimal | float | int,
        unit: str = "count",
        dimensions: dict | None = None,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
        recorded_at: datetime | None = None,
        **extra: Any,
    ) -> BusinessMetric:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        row = BusinessMetric(
            kpi_name=kpi_name,
            kpi_value=Decimal(str(kpi_value)),
            unit=unit,
            dimensions=dimensions,
            period_start=period_start,
            period_end=period_end,
            recorded_at=recorded_at or datetime.now(timezone.utc),
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_recent(
        self,
        *,
        kpi_name: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[BusinessMetric]:
        query = select(BusinessMetric)
        if kpi_name is not None:
            query = query.where(BusinessMetric.kpi_name == kpi_name)
        if since is not None:
            query = query.where(BusinessMetric.recorded_at >= since)
        result = await self._session.execute(
            query.order_by(BusinessMetric.recorded_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def latest_by_kpi(self, kpi_names: list[str]) -> dict[str, BusinessMetric]:
        latest: dict[str, BusinessMetric] = {}
        for name in kpi_names:
            result = await self._session.execute(
                select(BusinessMetric)
                .where(BusinessMetric.kpi_name == name)
                .order_by(BusinessMetric.recorded_at.desc())
                .limit(1)
            )
            row = result.scalar_one_or_none()
            if row is not None:
                latest[name] = row
        return latest


class ErrorEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        source: str,
        error_type: str,
        message: str,
        stack_trace: str | None = None,
        context: dict | None = None,
        severity: str = ErrorSeverity.ERROR.value,
        recorded_at: datetime | None = None,
        **extra: Any,
    ) -> ErrorEvent:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if severity not in {s.value for s in ErrorSeverity}:
            raise ValueError(f"Invalid severity: {severity}")

        row = ErrorEvent(
            source=source,
            error_type=error_type,
            message=message,
            stack_trace=stack_trace,
            context=context,
            severity=severity,
            recorded_at=recorded_at or datetime.now(timezone.utc),
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_recent(
        self,
        *,
        source: str | None = None,
        since: datetime | None = None,
        unresolved_only: bool = False,
        limit: int = 100,
    ) -> list[ErrorEvent]:
        query = select(ErrorEvent)
        if source is not None:
            query = query.where(ErrorEvent.source == source)
        if since is not None:
            query = query.where(ErrorEvent.recorded_at >= since)
        if unresolved_only:
            query = query.where(ErrorEvent.resolved.is_(False))
        result = await self._session.execute(
            query.order_by(ErrorEvent.recorded_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def count_since(
        self,
        *,
        since: datetime,
        source: str | None = None,
    ) -> int:
        query = select(func.count()).select_from(ErrorEvent).where(
            ErrorEvent.recorded_at >= since
        )
        if source is not None:
            query = query.where(ErrorEvent.source == source)
        result = await self._session.scalar(query)
        return int(result or 0)


class PerformanceMetricRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        operation_name: str,
        latency_ms: Decimal | float | int,
        success: bool = True,
        tags: dict | None = None,
        recorded_at: datetime | None = None,
        **extra: Any,
    ) -> PerformanceMetric:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        row = PerformanceMetric(
            operation_name=operation_name,
            latency_ms=Decimal(str(latency_ms)),
            success=success,
            tags=tags,
            recorded_at=recorded_at or datetime.now(timezone.utc),
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def aggregate_latency(
        self,
        *,
        operation_name: str,
        since: datetime,
    ) -> dict[str, Any]:
        result = await self._session.execute(
            select(
                func.count(PerformanceMetric.id),
                func.avg(PerformanceMetric.latency_ms),
                func.max(PerformanceMetric.latency_ms),
                func.percentile_cont(0.95).within_group(
                    PerformanceMetric.latency_ms.asc()
                ),
            ).where(
                PerformanceMetric.operation_name == operation_name,
                PerformanceMetric.recorded_at >= since,
                PerformanceMetric.success.is_(True),
            )
        )
        count, avg_ms, max_ms, p95_ms = result.one()
        failures = await self._session.scalar(
            select(func.count())
            .select_from(PerformanceMetric)
            .where(
                PerformanceMetric.operation_name == operation_name,
                PerformanceMetric.recorded_at >= since,
                PerformanceMetric.success.is_(False),
            )
        )
        total = (count or 0) + (failures or 0)
        error_rate = (failures or 0) / total if total else 0.0
        return {
            "count": count or 0,
            "avg_latency_ms": float(avg_ms) if avg_ms is not None else 0.0,
            "max_latency_ms": float(max_ms) if max_ms is not None else 0.0,
            "p95_latency_ms": float(p95_ms) if p95_ms is not None else 0.0,
            "error_rate": round(error_rate, 4),
            "failures": failures or 0,
        }
