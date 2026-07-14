# Universal Revenue Engine v1 repository.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import String, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.deal_engine_v1 import DealEngineV1Deal
from database.models.revenue_engine_v1 import RevenueEngineV1Entry


class RevenueEngineV1Repository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **fields) -> RevenueEngineV1Entry:
        row = RevenueEngineV1Entry(**fields)
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, entry_id: uuid.UUID) -> RevenueEngineV1Entry | None:
        result = await self._session.execute(
            select(RevenueEngineV1Entry).where(RevenueEngineV1Entry.id == entry_id)
        )
        return result.scalar_one_or_none()

    async def get_by_deal_id(self, deal_id: uuid.UUID) -> RevenueEngineV1Entry | None:
        result = await self._session.execute(
            select(RevenueEngineV1Entry).where(RevenueEngineV1Entry.deal_id == deal_id)
        )
        return result.scalar_one_or_none()

    async def sum_platform_income(self, *, since: datetime | None = None) -> Decimal:
        stmt = select(func.coalesce(func.sum(RevenueEngineV1Entry.platform_income), 0))
        if since is not None:
            stmt = stmt.where(RevenueEngineV1Entry.created_at >= since)
        result = await self._session.execute(stmt)
        return Decimal(result.scalar_one())

    async def sum_gross(self, *, since: datetime | None = None) -> Decimal:
        stmt = select(func.coalesce(func.sum(RevenueEngineV1Entry.gross_amount), 0))
        if since is not None:
            stmt = stmt.where(RevenueEngineV1Entry.created_at >= since)
        result = await self._session.execute(stmt)
        return Decimal(result.scalar_one())

    async def income_by_vertical(
        self,
        *,
        since: datetime | None = None,
    ) -> list[tuple[str, Decimal]]:
        stmt = (
            select(
                DealEngineV1Deal.vertical,
                func.coalesce(func.sum(RevenueEngineV1Entry.platform_income), 0),
            )
            .join(DealEngineV1Deal, DealEngineV1Deal.id == RevenueEngineV1Entry.deal_id)
            .group_by(DealEngineV1Deal.vertical)
            .order_by(func.sum(RevenueEngineV1Entry.platform_income).desc())
        )
        if since is not None:
            stmt = stmt.where(RevenueEngineV1Entry.created_at >= since)
        result = await self._session.execute(stmt)
        return [(row[0], Decimal(row[1])) for row in result.all()]

    async def income_by_partner(
        self,
        *,
        since: datetime | None = None,
        limit: int = 20,
    ) -> list[tuple[str | None, Decimal, Decimal]]:
        partner_key = func.coalesce(DealEngineV1Deal.partner_id.cast(String), "direct")
        stmt = (
            select(
                partner_key,
                func.coalesce(func.sum(RevenueEngineV1Entry.partner_income), 0),
                func.coalesce(func.sum(RevenueEngineV1Entry.platform_income), 0),
            )
            .join(DealEngineV1Deal, DealEngineV1Deal.id == RevenueEngineV1Entry.deal_id)
            .group_by(partner_key)
            .order_by(func.sum(RevenueEngineV1Entry.partner_income).desc())
            .limit(limit)
        )
        if since is not None:
            stmt = stmt.where(RevenueEngineV1Entry.created_at >= since)
        result = await self._session.execute(stmt)
        return [(row[0], Decimal(row[1]), Decimal(row[2])) for row in result.all()]

    async def list_recent(self, *, limit: int = 10) -> list[RevenueEngineV1Entry]:
        result = await self._session.execute(
            select(RevenueEngineV1Entry)
            .order_by(RevenueEngineV1Entry.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    def start_of_today() -> datetime:
        now = datetime.now(timezone.utc)
        return now.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def start_of_month() -> datetime:
        now = datetime.now(timezone.utc)
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
