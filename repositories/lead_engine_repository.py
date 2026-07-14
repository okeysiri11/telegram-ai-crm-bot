# Universal Lead Engine v1 repository.

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.lead_engine import (
    LEAD_ENGINE_TERMINAL_STATUSES,
    LeadEngineLead,
    LeadEngineStatus,
)


class LeadEngineRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, **fields) -> LeadEngineLead:
        row = LeadEngineLead(**fields)
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_id(self, lead_id: uuid.UUID) -> LeadEngineLead | None:
        result = await self._session.execute(
            select(LeadEngineLead).where(LeadEngineLead.id == lead_id)
        )
        return result.scalar_one_or_none()

    async def get_latest_for_telegram(
        self,
        telegram_user_id: int,
        *,
        source_link: str | None = None,
    ) -> LeadEngineLead | None:
        stmt = (
            select(LeadEngineLead)
            .where(LeadEngineLead.telegram_user_id == telegram_user_id)
            .order_by(LeadEngineLead.created_at.desc())
            .limit(1)
        )
        if source_link:
            stmt = stmt.where(LeadEngineLead.source_link == source_link)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, lead_id: uuid.UUID, **fields) -> LeadEngineLead | None:
        row = await self.get_by_id(lead_id)
        if row is None:
            return None
        for key, value in fields.items():
            setattr(row, key, value)
        await self._session.flush()
        return row

    async def assign_manager(
        self,
        lead_id: uuid.UUID,
        manager_id: uuid.UUID | None,
    ) -> LeadEngineLead | None:
        return await self.update(lead_id, assigned_manager_id=manager_id)

    async def count_since(self, since: datetime) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(LeadEngineLead)
            .where(LeadEngineLead.created_at >= since)
        )
        return int(result.scalar_one())

    async def count_by_status(self, status: str, *, since: datetime | None = None) -> int:
        stmt = select(func.count()).select_from(LeadEngineLead).where(LeadEngineLead.status == status)
        if since is not None:
            stmt = stmt.where(LeadEngineLead.created_at >= since)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

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
            .select_from(LeadEngineLead)
            .group_by(col)
            .order_by(func.count().desc())
            .limit(limit)
        )
        if since is not None:
            stmt = stmt.where(LeadEngineLead.created_at >= since)
        result = await self._session.execute(stmt)
        return [(row[0], int(row[1])) for row in result.all()]

    async def list_recent(self, *, limit: int = 20) -> list[LeadEngineLead]:
        result = await self._session.execute(
            select(LeadEngineLead)
            .order_by(LeadEngineLead.created_at.desc())
            .limit(limit)
        )
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
