# Financial Settlement Engine v1 repository.

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.financial_settlement_engine_v1 import (
    FinancialCommissionRecipientType,
    FinancialCommissionStatus,
    FinancialSettlementStatus,
    FinancialSettlementV1Commission,
    FinancialSettlementV1Revenue,
    FinancialSettlementV1Settlement,
    FinancialSettlementV1TreasuryTransaction,
)


class FinancialSettlementV1Repository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def start_of_today() -> datetime:
        now = datetime.now(timezone.utc)
        return now.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def start_of_week() -> datetime:
        today = FinancialSettlementV1Repository.start_of_today()
        return today - timedelta(days=today.weekday())

    @staticmethod
    def start_of_month() -> datetime:
        now = datetime.now(timezone.utc)
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    async def get_revenue_by_payment(self, payment_id: uuid.UUID) -> FinancialSettlementV1Revenue | None:
        result = await self._session.execute(
            select(FinancialSettlementV1Revenue).where(
                FinancialSettlementV1Revenue.payment_id == payment_id
            )
        )
        return result.scalar_one_or_none()

    async def get_settlement_by_payment(
        self,
        payment_id: uuid.UUID,
    ) -> FinancialSettlementV1Settlement | None:
        result = await self._session.execute(
            select(FinancialSettlementV1Settlement).where(
                FinancialSettlementV1Settlement.payment_id == payment_id
            )
        )
        return result.scalar_one_or_none()

    async def create_revenue(self, **fields) -> FinancialSettlementV1Revenue:
        row = FinancialSettlementV1Revenue(**fields)
        self._session.add(row)
        await self._session.flush()
        return row

    async def create_settlement(self, **fields) -> FinancialSettlementV1Settlement:
        row = FinancialSettlementV1Settlement(**fields)
        self._session.add(row)
        await self._session.flush()
        return row

    async def create_commission(self, **fields) -> FinancialSettlementV1Commission:
        row = FinancialSettlementV1Commission(**fields)
        self._session.add(row)
        await self._session.flush()
        return row

    async def create_treasury_transaction(
        self,
        **fields,
    ) -> FinancialSettlementV1TreasuryTransaction:
        row = FinancialSettlementV1TreasuryTransaction(**fields)
        self._session.add(row)
        await self._session.flush()
        return row

    async def sum_revenue(self, *, since: datetime | None = None) -> Decimal:
        stmt = select(func.coalesce(func.sum(FinancialSettlementV1Revenue.gross_amount), 0))
        if since is not None:
            stmt = stmt.where(FinancialSettlementV1Revenue.created_at >= since)
        result = await self._session.execute(stmt)
        return Decimal(result.scalar_one())

    async def count_pending_settlements(self) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(FinancialSettlementV1Settlement)
            .where(FinancialSettlementV1Settlement.status == FinancialSettlementStatus.PENDING.value)
        )
        return int(result.scalar_one())

    async def sum_partner_liabilities(self) -> Decimal:
        result = await self._session.execute(
            select(func.coalesce(func.sum(FinancialSettlementV1Commission.amount), 0))
            .where(
                FinancialSettlementV1Commission.recipient_type
                == FinancialCommissionRecipientType.PARTNER.value,
                FinancialSettlementV1Commission.status.in_(
                    (
                        FinancialCommissionStatus.ACCRUED.value,
                        FinancialCommissionStatus.PENDING_PAYOUT.value,
                    )
                ),
            )
        )
        return Decimal(result.scalar_one())

    async def sum_manager_commissions(self) -> Decimal:
        result = await self._session.execute(
            select(func.coalesce(func.sum(FinancialSettlementV1Commission.amount), 0))
            .where(
                FinancialSettlementV1Commission.recipient_type.in_(
                    (
                        FinancialCommissionRecipientType.MANAGER.value,
                        FinancialCommissionRecipientType.REFERRAL.value,
                    )
                ),
                FinancialSettlementV1Commission.status.in_(
                    (
                        FinancialCommissionStatus.ACCRUED.value,
                        FinancialCommissionStatus.PENDING_PAYOUT.value,
                    )
                ),
            )
        )
        return Decimal(result.scalar_one())

    async def list_recent_settlements(self, *, limit: int = 5) -> list[FinancialSettlementV1Settlement]:
        result = await self._session.execute(
            select(FinancialSettlementV1Settlement)
            .order_by(FinancialSettlementV1Settlement.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_commissions_for_settlement(
        self,
        settlement_id: uuid.UUID,
    ) -> list[FinancialSettlementV1Commission]:
        result = await self._session.execute(
            select(FinancialSettlementV1Commission).where(
                FinancialSettlementV1Commission.settlement_id == settlement_id
            )
        )
        return list(result.scalars().all())

    async def list_treasury_for_settlement(
        self,
        settlement_id: uuid.UUID,
    ) -> list[FinancialSettlementV1TreasuryTransaction]:
        result = await self._session.execute(
            select(FinancialSettlementV1TreasuryTransaction).where(
                FinancialSettlementV1TreasuryTransaction.settlement_id == settlement_id
            )
        )
        return list(result.scalars().all())
