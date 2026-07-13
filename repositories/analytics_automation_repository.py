# Analytics Automation Engine v1 repository.

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.analytics_automation_engine import (
    SNAPSHOT_PERIODS,
    AnalyticsSnapshot,
    SnapshotPeriod,
)


class AnalyticsAutomationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_snapshot(
        self,
        *,
        metric_date: date,
        metrics: dict[str, Any],
        period: str = SnapshotPeriod.DAILY.value,
    ) -> AnalyticsSnapshot:
        if period not in SNAPSHOT_PERIODS:
            raise ValueError(f"Invalid period: {period}")

        result = await self._session.execute(
            select(AnalyticsSnapshot).where(
                AnalyticsSnapshot.metric_date == metric_date,
                AnalyticsSnapshot.period == period,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            existing.metrics = metrics
            await self._session.flush()
            return existing

        snapshot = AnalyticsSnapshot(
            metric_date=metric_date,
            period=period,
            metrics=metrics,
        )
        self._session.add(snapshot)
        await self._session.flush()
        return snapshot

    async def get_snapshot(
        self,
        metric_date: date,
        *,
        period: str = SnapshotPeriod.DAILY.value,
    ) -> AnalyticsSnapshot | None:
        result = await self._session.execute(
            select(AnalyticsSnapshot).where(
                AnalyticsSnapshot.metric_date == metric_date,
                AnalyticsSnapshot.period == period,
            )
        )
        return result.scalar_one_or_none()

    async def list_snapshots(
        self,
        *,
        limit: int = 30,
    ) -> list[AnalyticsSnapshot]:
        result = await self._session.execute(
            select(AnalyticsSnapshot)
            .order_by(AnalyticsSnapshot.metric_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    def snapshot_dict(row: AnalyticsSnapshot) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "metric_date": row.metric_date.isoformat(),
            "period": row.period,
            "metrics": row.metrics,
            "created_at": row.created_at.isoformat(),
            "updated_at": row.updated_at.isoformat(),
        }
