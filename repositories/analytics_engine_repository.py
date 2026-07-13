# Analytics Engine v1 repositories.

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.analytics_engine import (
    AdvertisingStatistics,
    LeadStatistics,
    ManagerStatistics,
    SalesStatistics,
)


class LeadStatisticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        metric_date: date,
        total_leads: int = 0,
        qualified_leads: int = 0,
        leads_by_source: dict | None = None,
        cpl: Decimal | None = None,
        conversion_rate: Decimal | None = None,
        lead_source_roi: dict | None = None,
        metadata: dict | None = None,
    ) -> LeadStatistics:
        result = await self._session.execute(
            select(LeadStatistics).where(
                LeadStatistics.tenant_id == tenant_id,
                LeadStatistics.metric_date == metric_date,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = LeadStatistics(
                tenant_id=tenant_id,
                company_id=company_id,
                metric_date=metric_date,
            )
            self._session.add(row)
        row.total_leads = total_leads
        row.qualified_leads = qualified_leads
        row.leads_by_source = leads_by_source
        row.cpl = cpl
        row.conversion_rate = conversion_rate
        row.lead_source_roi = lead_source_roi
        row.metadata_ = metadata
        await self._session.flush()
        return row

    async def get_by_date(
        self,
        tenant_id: uuid.UUID,
        metric_date: date,
    ) -> LeadStatistics | None:
        result = await self._session.execute(
            select(LeadStatistics).where(
                LeadStatistics.tenant_id == tenant_id,
                LeadStatistics.metric_date == metric_date,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_tenant(
        self,
        tenant_id: uuid.UUID,
        *,
        limit: int = 30,
    ) -> list[LeadStatistics]:
        result = await self._session.execute(
            select(LeadStatistics)
            .where(LeadStatistics.tenant_id == tenant_id)
            .order_by(LeadStatistics.metric_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class SalesStatisticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        metric_date: date,
        deals_won: int = 0,
        deals_lost: int = 0,
        total_revenue: Decimal | None = None,
        average_deal_size: Decimal | None = None,
        conversion_rate: Decimal | None = None,
        vehicle_turnover: Decimal | None = None,
        metadata: dict | None = None,
    ) -> SalesStatistics:
        result = await self._session.execute(
            select(SalesStatistics).where(
                SalesStatistics.tenant_id == tenant_id,
                SalesStatistics.metric_date == metric_date,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = SalesStatistics(
                tenant_id=tenant_id,
                company_id=company_id,
                metric_date=metric_date,
            )
            self._session.add(row)
        row.deals_won = deals_won
        row.deals_lost = deals_lost
        row.total_revenue = total_revenue
        row.average_deal_size = average_deal_size
        row.conversion_rate = conversion_rate
        row.vehicle_turnover = vehicle_turnover
        row.metadata_ = metadata
        await self._session.flush()
        return row

    async def get_by_date(
        self,
        tenant_id: uuid.UUID,
        metric_date: date,
    ) -> SalesStatistics | None:
        result = await self._session.execute(
            select(SalesStatistics).where(
                SalesStatistics.tenant_id == tenant_id,
                SalesStatistics.metric_date == metric_date,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_tenant(
        self,
        tenant_id: uuid.UUID,
        *,
        limit: int = 30,
    ) -> list[SalesStatistics]:
        result = await self._session.execute(
            select(SalesStatistics)
            .where(SalesStatistics.tenant_id == tenant_id)
            .order_by(SalesStatistics.metric_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class AdvertisingStatisticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        metric_date: date,
        total_spend: Decimal | None = None,
        total_impressions: int = 0,
        total_clicks: int = 0,
        leads_from_ads: int = 0,
        cac: Decimal | None = None,
        cpl: Decimal | None = None,
        campaign_metrics: dict | None = None,
        metadata: dict | None = None,
    ) -> AdvertisingStatistics:
        result = await self._session.execute(
            select(AdvertisingStatistics).where(
                AdvertisingStatistics.tenant_id == tenant_id,
                AdvertisingStatistics.metric_date == metric_date,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = AdvertisingStatistics(
                tenant_id=tenant_id,
                company_id=company_id,
                metric_date=metric_date,
            )
            self._session.add(row)
        row.total_spend = total_spend
        row.total_impressions = total_impressions
        row.total_clicks = total_clicks
        row.leads_from_ads = leads_from_ads
        row.cac = cac
        row.cpl = cpl
        row.campaign_metrics = campaign_metrics
        row.metadata_ = metadata
        await self._session.flush()
        return row

    async def list_by_tenant(
        self,
        tenant_id: uuid.UUID,
        *,
        limit: int = 30,
    ) -> list[AdvertisingStatistics]:
        result = await self._session.execute(
            select(AdvertisingStatistics)
            .where(AdvertisingStatistics.tenant_id == tenant_id)
            .order_by(AdvertisingStatistics.metric_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class ManagerStatisticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        manager_id: int,
        metric_date: date,
        leads_assigned: int = 0,
        deals_closed: int = 0,
        revenue: Decimal | None = None,
        conversion_rate: Decimal | None = None,
        performance_score: Decimal | None = None,
        metadata: dict | None = None,
    ) -> ManagerStatistics:
        result = await self._session.execute(
            select(ManagerStatistics).where(
                ManagerStatistics.tenant_id == tenant_id,
                ManagerStatistics.manager_id == manager_id,
                ManagerStatistics.metric_date == metric_date,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = ManagerStatistics(
                tenant_id=tenant_id,
                company_id=company_id,
                manager_id=manager_id,
                metric_date=metric_date,
            )
            self._session.add(row)
        row.leads_assigned = leads_assigned
        row.deals_closed = deals_closed
        row.revenue = revenue
        row.conversion_rate = conversion_rate
        row.performance_score = performance_score
        row.metadata_ = metadata
        await self._session.flush()
        return row

    async def list_by_tenant(
        self,
        tenant_id: uuid.UUID,
        *,
        metric_date: date | None = None,
        limit: int = 50,
    ) -> list[ManagerStatistics]:
        stmt = (
            select(ManagerStatistics)
            .where(ManagerStatistics.tenant_id == tenant_id)
            .order_by(ManagerStatistics.metric_date.desc(), ManagerStatistics.manager_id.asc())
            .limit(limit)
        )
        if metric_date is not None:
            stmt = stmt.where(ManagerStatistics.metric_date == metric_date)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def snapshot(row: ManagerStatistics) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "manager_id": row.manager_id,
            "metric_date": row.metric_date.isoformat(),
            "leads_assigned": row.leads_assigned,
            "deals_closed": row.deals_closed,
            "revenue": str(row.revenue) if row.revenue is not None else None,
            "conversion_rate": str(row.conversion_rate) if row.conversion_rate is not None else None,
            "performance_score": (
                str(row.performance_score) if row.performance_score is not None else None
            ),
        }

    @staticmethod
    def lead_snapshot(row: LeadStatistics) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "metric_date": row.metric_date.isoformat(),
            "total_leads": row.total_leads,
            "qualified_leads": row.qualified_leads,
            "leads_by_source": row.leads_by_source,
            "cpl": str(row.cpl) if row.cpl is not None else None,
            "conversion_rate": (
                str(row.conversion_rate) if row.conversion_rate is not None else None
            ),
            "lead_source_roi": row.lead_source_roi,
        }

    @staticmethod
    def sales_snapshot(row: SalesStatistics) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "metric_date": row.metric_date.isoformat(),
            "deals_won": row.deals_won,
            "deals_lost": row.deals_lost,
            "total_revenue": str(row.total_revenue) if row.total_revenue is not None else None,
            "average_deal_size": (
                str(row.average_deal_size) if row.average_deal_size is not None else None
            ),
            "conversion_rate": (
                str(row.conversion_rate) if row.conversion_rate is not None else None
            ),
            "vehicle_turnover": (
                str(row.vehicle_turnover) if row.vehicle_turnover is not None else None
            ),
        }

    @staticmethod
    def advertising_snapshot(row: AdvertisingStatistics) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "metric_date": row.metric_date.isoformat(),
            "total_spend": str(row.total_spend) if row.total_spend is not None else None,
            "total_impressions": row.total_impressions,
            "total_clicks": row.total_clicks,
            "leads_from_ads": row.leads_from_ads,
            "cac": str(row.cac) if row.cac is not None else None,
            "cpl": str(row.cpl) if row.cpl is not None else None,
            "campaign_metrics": row.campaign_metrics,
        }
