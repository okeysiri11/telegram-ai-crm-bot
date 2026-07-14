# Universal Deal Engine v1 repository.

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.deal_engine_v1 import DealEngineV1Deal, DealEngineV1Status


class DealEngineV1Repository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **fields) -> DealEngineV1Deal:
        row = DealEngineV1Deal(**fields)
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, deal_id: uuid.UUID) -> DealEngineV1Deal | None:
        result = await self._session.execute(
            select(DealEngineV1Deal).where(DealEngineV1Deal.id == deal_id)
        )
        return result.scalar_one_or_none()

    async def get_by_lead_id(self, lead_id: uuid.UUID) -> DealEngineV1Deal | None:
        result = await self._session.execute(
            select(DealEngineV1Deal)
            .where(DealEngineV1Deal.lead_id == lead_id)
            .order_by(DealEngineV1Deal.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update(self, deal_id: uuid.UUID, **fields) -> DealEngineV1Deal | None:
        row = await self.get_by_id(deal_id)
        if row is None:
            return None
        for key, value in fields.items():
            setattr(row, key, value)
        await self._session.flush()
        return row

    async def attach_partner(
        self,
        deal_id: uuid.UUID,
        partner_id: uuid.UUID | None,
    ) -> DealEngineV1Deal | None:
        return await self.update(deal_id, partner_id=partner_id)

    async def count_since(self, since: datetime | None = None) -> int:
        stmt = select(func.count()).select_from(DealEngineV1Deal)
        if since is not None:
            stmt = stmt.where(DealEngineV1Deal.created_at >= since)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def count_by_status(self, status: str, *, since: datetime | None = None) -> int:
        stmt = select(func.count()).select_from(DealEngineV1Deal).where(DealEngineV1Deal.status == status)
        if since is not None:
            stmt = stmt.where(DealEngineV1Deal.created_at >= since)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def sum_amount(
        self,
        *,
        vertical: str | None = None,
        since: datetime | None = None,
        statuses: frozenset[str] | None = None,
    ) -> Decimal:
        stmt = select(func.coalesce(func.sum(DealEngineV1Deal.amount), 0)).select_from(DealEngineV1Deal)
        if vertical:
            stmt = stmt.where(DealEngineV1Deal.vertical == vertical)
        if since is not None:
            stmt = stmt.where(DealEngineV1Deal.created_at >= since)
        if statuses:
            stmt = stmt.where(DealEngineV1Deal.status.in_(statuses))
        result = await self._session.execute(stmt)
        return Decimal(result.scalar_one())

    async def group_count(
        self,
        column,
        *,
        since: datetime | None = None,
        limit: int = 20,
    ) -> list[tuple[str | None, int]]:
        col = column.label("bucket")
        stmt = (
            select(col, func.count())
            .select_from(DealEngineV1Deal)
            .group_by(col)
            .order_by(func.count().desc())
            .limit(limit)
        )
        if since is not None:
            stmt = stmt.where(DealEngineV1Deal.created_at >= since)
        result = await self._session.execute(stmt)
        return [(row[0], int(row[1])) for row in result.all()]

    async def list_recent(self, *, limit: int = 20, vertical: str | None = None) -> list[DealEngineV1Deal]:
        stmt = select(DealEngineV1Deal).order_by(DealEngineV1Deal.created_at.desc()).limit(limit)
        if vertical:
            stmt = stmt.where(DealEngineV1Deal.vertical == vertical)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    def start_of_today() -> datetime:
        now = datetime.now(timezone.utc)
        return now.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def start_of_week() -> datetime:
        now = datetime.now(timezone.utc)
        return (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
