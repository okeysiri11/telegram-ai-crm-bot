# Production Readiness Suite repositories.

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.production_readiness_engine import (
    ALERT_SEVERITIES,
    HEALTH_CHECK_STATUSES,
    SystemAlert,
    SystemHealth,
    SystemMetric,
)


class SystemHealthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        check_name: str,
        status: str,
        checked_at: datetime,
        detail: str | None = None,
        payload: dict | None = None,
        suite_version: str = "v1",
    ) -> SystemHealth:
        if status not in HEALTH_CHECK_STATUSES:
            raise ValueError(f"Invalid status: {status}")
        row = SystemHealth(
            check_name=check_name,
            status=status,
            detail=detail,
            payload=payload,
            checked_at=checked_at,
            suite_version=suite_version,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def latest_by_check(self, check_name: str) -> SystemHealth | None:
        result = await self._session.execute(
            select(SystemHealth)
            .where(SystemHealth.check_name == check_name)
            .order_by(SystemHealth.checked_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def latest_snapshot(self, *, limit: int = 20) -> list[SystemHealth]:
        result = await self._session.execute(
            select(SystemHealth).order_by(SystemHealth.checked_at.desc()).limit(limit)
        )
        return list(result.scalars().all())


class SystemMetricRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        metric_name: str,
        metric_value: Decimal | float | int,
        recorded_at: datetime,
        unit: str = "count",
        tags: dict | None = None,
    ) -> SystemMetric:
        row = SystemMetric(
            metric_name=metric_name,
            metric_value=Decimal(str(metric_value)),
            unit=unit,
            tags=tags,
            recorded_at=recorded_at,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def latest_by_name(self, metric_name: str) -> SystemMetric | None:
        result = await self._session.execute(
            select(SystemMetric)
            .where(SystemMetric.metric_name == metric_name)
            .order_by(SystemMetric.recorded_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class SystemAlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        alert_type: str,
        severity: str,
        component: str,
        message: str,
        payload: dict | None = None,
    ) -> SystemAlert:
        if severity not in ALERT_SEVERITIES:
            raise ValueError(f"Invalid severity: {severity}")
        row = SystemAlert(
            alert_type=alert_type,
            severity=severity,
            component=component,
            message=message,
            payload=payload,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_unresolved(self, *, limit: int = 50) -> list[SystemAlert]:
        result = await self._session.execute(
            select(SystemAlert)
            .where(SystemAlert.resolved_at.is_(None))
            .order_by(SystemAlert.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def resolve_for_component(self, component: str, *, resolved_at: datetime) -> int:
        result = await self._session.execute(
            update(SystemAlert)
            .where(
                SystemAlert.component == component,
                SystemAlert.resolved_at.is_(None),
            )
            .values(resolved_at=resolved_at)
        )
        return int(result.rowcount or 0)

    async def count_unresolved(self) -> dict[str, int]:
        result = await self._session.execute(
            select(SystemAlert.severity, func.count())
            .where(SystemAlert.resolved_at.is_(None))
            .group_by(SystemAlert.severity)
        )
        return {severity: count for severity, count in result.all()}
