# Commission Engine repository — PostgreSQL async data access.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.commission import (
    CommissionStatus,
    CommissionType,
    DealEngineCommission,
)


class CommissionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        deal_id: uuid.UUID,
        commission_type: str,
        asset: str,
        amount: Decimal,
        manager_id: int | None = None,
        partner_id: int | None = None,
        percentage: Decimal | None = None,
        status: str = CommissionStatus.PENDING.value,
        **extra: Any,
    ) -> DealEngineCommission:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        if commission_type not in {t.value for t in CommissionType}:
            raise ValueError(f"Invalid commission_type: {commission_type}")
        if status not in {s.value for s in CommissionStatus}:
            raise ValueError(f"Invalid status: {status}")
        if amount < 0:
            raise ValueError("amount must be non-negative")

        commission = DealEngineCommission(
            deal_id=deal_id,
            manager_id=manager_id,
            partner_id=partner_id,
            commission_type=commission_type,
            asset=asset,
            percentage=percentage,
            amount=amount,
            status=status,
        )
        self._session.add(commission)
        await self._session.flush()
        return commission

    async def get_by_deal(self, deal_id: uuid.UUID) -> list[DealEngineCommission]:
        result = await self._session.execute(
            select(DealEngineCommission)
            .where(DealEngineCommission.deal_id == deal_id)
            .order_by(DealEngineCommission.created_at.asc())
        )
        return list(result.scalars().all())

    async def list_pending(self, *, limit: int = 100) -> list[DealEngineCommission]:
        result = await self._session.execute(
            select(DealEngineCommission)
            .where(DealEngineCommission.status == CommissionStatus.PENDING.value)
            .order_by(DealEngineCommission.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_paid(self, commission_id: uuid.UUID) -> DealEngineCommission | None:
        result = await self._session.execute(
            select(DealEngineCommission).where(DealEngineCommission.id == commission_id)
        )
        commission = result.scalar_one_or_none()
        if commission is None:
            return None

        commission.status = CommissionStatus.PAID.value
        commission.paid_at = datetime.now(timezone.utc)
        await self._session.flush()
        return commission

    async def calculate_company_profit(self, deal_id: uuid.UUID) -> Decimal:
        result = await self._session.execute(
            select(DealEngineCommission.commission_type, func.sum(DealEngineCommission.amount))
            .where(
                DealEngineCommission.deal_id == deal_id,
                DealEngineCommission.status != CommissionStatus.CANCELLED.value,
            )
            .group_by(DealEngineCommission.commission_type)
        )
        totals = {row[0]: Decimal(row[1] or 0) for row in result.all()}

        client_fee = totals.get(CommissionType.CLIENT_FEE.value, Decimal(0))
        manager_reward = totals.get(CommissionType.MANAGER_REWARD.value, Decimal(0))
        partner_reward = totals.get(CommissionType.PARTNER_REWARD.value, Decimal(0))
        recorded_profit = totals.get(CommissionType.COMPANY_PROFIT.value, Decimal(0))

        if recorded_profit > 0:
            return recorded_profit
        return client_fee - manager_reward - partner_reward
