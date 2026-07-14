# Owner Dashboard v1 — cross-engine aggregation queries.

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import String, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.deal_engine_v1 import DealEngineV1Deal, DealEngineV1Status
from database.models.lead_engine import LeadEngineLead
from database.models.revenue_engine_v1 import RevenueEngineV1Entry


class OwnerDashboardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def count_leads(
        self,
        *,
        vertical: str | None = None,
        since: datetime | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(LeadEngineLead)
        if vertical:
            stmt = stmt.where(LeadEngineLead.vertical == vertical)
        if since is not None:
            stmt = stmt.where(LeadEngineLead.created_at >= since)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def count_deals(
        self,
        *,
        vertical: str | None = None,
        since: datetime | None = None,
        status: str | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(DealEngineV1Deal)
        if vertical:
            stmt = stmt.where(DealEngineV1Deal.vertical == vertical)
        if since is not None:
            stmt = stmt.where(DealEngineV1Deal.created_at >= since)
        if status:
            stmt = stmt.where(DealEngineV1Deal.status == status)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def sum_revenue_platform(
        self,
        *,
        vertical: str | None = None,
        since: datetime | None = None,
    ) -> Decimal:
        stmt = select(func.coalesce(func.sum(RevenueEngineV1Entry.platform_income), 0))
        if vertical or since:
            stmt = stmt.join(DealEngineV1Deal, DealEngineV1Deal.id == RevenueEngineV1Entry.deal_id)
        if vertical:
            stmt = stmt.where(DealEngineV1Deal.vertical == vertical)
        if since is not None:
            stmt = stmt.where(RevenueEngineV1Entry.created_at >= since)
        result = await self._session.execute(stmt)
        return Decimal(result.scalar_one())

    async def sum_commissions(self, *, since: datetime | None = None) -> Decimal:
        stmt = select(
            func.coalesce(
                func.sum(
                    RevenueEngineV1Entry.partner_income
                    + RevenueEngineV1Entry.manager_income
                    + RevenueEngineV1Entry.referral_income
                ),
                0,
            )
        )
        if since is not None:
            stmt = stmt.where(RevenueEngineV1Entry.created_at >= since)
        result = await self._session.execute(stmt)
        return Decimal(result.scalar_one())

    async def top_partners(
        self,
        *,
        since: datetime | None = None,
        limit: int = 5,
    ) -> list[tuple[str, Decimal, int]]:
        partner_key = func.coalesce(DealEngineV1Deal.partner_id.cast(String), "direct")
        stmt = (
            select(
                partner_key,
                func.coalesce(func.sum(RevenueEngineV1Entry.partner_income), 0),
                func.count(DealEngineV1Deal.id),
            )
            .join(DealEngineV1Deal, DealEngineV1Deal.id == RevenueEngineV1Entry.deal_id)
            .group_by(partner_key)
            .order_by(func.sum(RevenueEngineV1Entry.partner_income).desc())
            .limit(limit)
        )
        if since is not None:
            stmt = stmt.where(RevenueEngineV1Entry.created_at >= since)
        result = await self._session.execute(stmt)
        return [(row[0], Decimal(row[1]), int(row[2])) for row in result.all()]

    async def top_managers(
        self,
        *,
        since: datetime | None = None,
        limit: int = 5,
    ) -> list[tuple[str, Decimal, int]]:
        manager_key = func.coalesce(DealEngineV1Deal.manager_id.cast(String), "unassigned")
        stmt = (
            select(
                manager_key,
                func.coalesce(func.sum(RevenueEngineV1Entry.manager_income), 0),
                func.count(DealEngineV1Deal.id),
            )
            .join(DealEngineV1Deal, DealEngineV1Deal.id == RevenueEngineV1Entry.deal_id)
            .group_by(manager_key)
            .order_by(func.sum(RevenueEngineV1Entry.manager_income).desc())
            .limit(limit)
        )
        if since is not None:
            stmt = stmt.where(RevenueEngineV1Entry.created_at >= since)
        result = await self._session.execute(stmt)
        return [(row[0], Decimal(row[1]), int(row[2])) for row in result.all()]

    async def leads_by_source(
        self,
        *,
        since: datetime | None = None,
        limit: int = 10,
    ) -> list[tuple[str | None, int]]:
        col = LeadEngineLead.source_link.label("source")
        stmt = (
            select(col, func.count())
            .group_by(col)
            .order_by(func.count().desc())
            .limit(limit)
        )
        if since is not None:
            stmt = stmt.where(LeadEngineLead.created_at >= since)
        result = await self._session.execute(stmt)
        return [(row[0], int(row[1])) for row in result.all()]

    async def leads_by_utm(
        self,
        *,
        since: datetime | None = None,
        limit: int = 10,
    ) -> list[tuple[str | None, int]]:
        col = LeadEngineLead.utm_source.label("utm")
        stmt = (
            select(col, func.count())
            .group_by(col)
            .order_by(func.count().desc())
            .limit(limit)
        )
        if since is not None:
            stmt = stmt.where(LeadEngineLead.created_at >= since)
        result = await self._session.execute(stmt)
        return [(row[0], int(row[1])) for row in result.all()]

    async def revenue_breakdown(self, *, since: datetime | None = None) -> dict[str, Decimal]:
        stmt = select(
            func.coalesce(func.sum(RevenueEngineV1Entry.gross_amount), 0),
            func.coalesce(func.sum(RevenueEngineV1Entry.platform_income), 0),
            func.coalesce(func.sum(RevenueEngineV1Entry.partner_income), 0),
            func.coalesce(func.sum(RevenueEngineV1Entry.manager_income), 0),
            func.coalesce(func.sum(RevenueEngineV1Entry.referral_income), 0),
        )
        if since is not None:
            stmt = stmt.where(RevenueEngineV1Entry.created_at >= since)
        result = await self._session.execute(stmt)
        row = result.one()
        return {
            "gross": Decimal(row[0]),
            "platform": Decimal(row[1]),
            "partner": Decimal(row[2]),
            "manager": Decimal(row[3]),
            "referral": Decimal(row[4]),
        }

    @staticmethod
    def start_of_today() -> datetime:
        now = datetime.now(timezone.utc)
        return now.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def start_of_month() -> datetime:
        now = datetime.now(timezone.utc)
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
