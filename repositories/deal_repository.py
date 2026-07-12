# Deal Engine repository — PostgreSQL async data access.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.deal import TERMINAL_DEAL_STATUSES, Deal, DealStatus


class DealRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        client_id: int | None = None,
        manager_id: int | None = None,
        partner_id: int | None = None,
        asset_in_type: str | None = None,
        asset_in_amount: Decimal | None = None,
        asset_out_type: str | None = None,
        asset_out_amount: Decimal | None = None,
        exchange_rate: Decimal | None = None,
        commission_amount: Decimal | None = None,
        commission_currency: str | None = None,
        status: str = DealStatus.NEW.value,
        **extra: Any,
    ) -> Deal:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        deal = Deal(
            client_id=client_id,
            manager_id=manager_id,
            partner_id=partner_id,
            asset_in_type=asset_in_type,
            asset_in_amount=asset_in_amount,
            asset_out_type=asset_out_type,
            asset_out_amount=asset_out_amount,
            exchange_rate=exchange_rate,
            commission_amount=commission_amount,
            commission_currency=commission_currency,
            status=status,
        )
        self._session.add(deal)
        await self._session.flush()
        return deal

    async def get_by_id(self, deal_id: uuid.UUID) -> Deal | None:
        result = await self._session.execute(
            select(Deal).where(Deal.id == deal_id)
        )
        return result.scalar_one_or_none()

    async def update_status(self, deal_id: uuid.UUID, status: str) -> Deal | None:
        deal = await self.get_by_id(deal_id)
        if deal is None:
            return None

        deal.status = status
        if status == DealStatus.COMPLETED.value:
            deal.completed_at = datetime.now(timezone.utc)
        elif status in TERMINAL_DEAL_STATUSES and deal.completed_at is None:
            deal.completed_at = datetime.now(timezone.utc)

        await self._session.flush()
        return deal

    async def list_active(self, *, limit: int = 100) -> list[Deal]:
        result = await self._session.execute(
            select(Deal)
            .where(Deal.status.not_in(TERMINAL_DEAL_STATUSES))
            .order_by(Deal.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_manager(
        self,
        manager_id: int,
        *,
        active_only: bool = False,
        limit: int = 100,
    ) -> list[Deal]:
        stmt = select(Deal).where(Deal.manager_id == manager_id)
        if active_only:
            stmt = stmt.where(Deal.status.not_in(TERMINAL_DEAL_STATUSES))
        stmt = stmt.order_by(Deal.created_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
