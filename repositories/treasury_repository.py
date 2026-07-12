# Treasury Engine repository — PostgreSQL async data access.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.treasury import (
    LiquidityReservation,
    LiquidityReservationStatus,
    TreasuryAccount,
    TreasuryAccountStatus,
    TreasuryAccountType,
    TreasuryTransfer,
    TreasuryTransferStatus,
    TreasuryTransferType,
)


class TreasuryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_account(
        self,
        *,
        code: str,
        name: str,
        asset: str,
        account_type: str = TreasuryAccountType.OPERATING.value,
        balance: Decimal = Decimal("0"),
        status: str = TreasuryAccountStatus.ACTIVE.value,
        **extra: Any,
    ) -> TreasuryAccount:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if account_type not in {t.value for t in TreasuryAccountType}:
            raise ValueError(f"Invalid account_type: {account_type}")
        if status not in {s.value for s in TreasuryAccountStatus}:
            raise ValueError(f"Invalid status: {status}")
        if balance < 0:
            raise ValueError("balance must be non-negative")

        account = TreasuryAccount(
            code=code,
            name=name,
            asset=asset,
            account_type=account_type,
            balance=balance,
            reserved_balance=Decimal("0"),
            status=status,
        )
        self._session.add(account)
        await self._session.flush()
        return account

    async def get_account(self, account_id: uuid.UUID) -> TreasuryAccount | None:
        result = await self._session.execute(
            select(TreasuryAccount).where(TreasuryAccount.id == account_id)
        )
        return result.scalar_one_or_none()

    async def get_account_for_update(self, account_id: uuid.UUID) -> TreasuryAccount | None:
        result = await self._session.execute(
            select(TreasuryAccount)
            .where(TreasuryAccount.id == account_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def list_accounts(
        self,
        *,
        asset: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[TreasuryAccount]:
        stmt = select(TreasuryAccount).order_by(TreasuryAccount.code.asc()).limit(limit)
        if asset is not None:
            stmt = stmt.where(TreasuryAccount.asset == asset)
        if status is not None:
            stmt = stmt.where(TreasuryAccount.status == status)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_transfer(
        self,
        *,
        from_account_id: uuid.UUID,
        to_account_id: uuid.UUID,
        asset: str,
        amount: Decimal,
        transfer_type: str = TreasuryTransferType.INTERNAL.value,
        status: str = TreasuryTransferStatus.PENDING.value,
        deal_id: uuid.UUID | None = None,
        reference: str | None = None,
        description: str | None = None,
        **extra: Any,
    ) -> TreasuryTransfer:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if transfer_type not in {t.value for t in TreasuryTransferType}:
            raise ValueError(f"Invalid transfer_type: {transfer_type}")
        if status not in {s.value for s in TreasuryTransferStatus}:
            raise ValueError(f"Invalid status: {status}")
        if amount <= 0:
            raise ValueError("amount must be positive")
        if from_account_id == to_account_id:
            raise ValueError("from_account_id and to_account_id must differ")

        transfer = TreasuryTransfer(
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            deal_id=deal_id,
            asset=asset,
            amount=amount,
            transfer_type=transfer_type,
            status=status,
            reference=reference,
            description=description,
        )
        self._session.add(transfer)
        await self._session.flush()
        return transfer

    async def complete_transfer(self, transfer_id: uuid.UUID) -> TreasuryTransfer | None:
        result = await self._session.execute(
            select(TreasuryTransfer).where(TreasuryTransfer.id == transfer_id)
        )
        transfer = result.scalar_one_or_none()
        if transfer is None:
            return None

        transfer.status = TreasuryTransferStatus.COMPLETED.value
        transfer.completed_at = datetime.now(timezone.utc)
        await self._session.flush()
        return transfer

    async def create_reservation(
        self,
        *,
        account_id: uuid.UUID,
        asset: str,
        amount: Decimal,
        deal_id: uuid.UUID | None = None,
        reference: str | None = None,
        description: str | None = None,
        **extra: Any,
    ) -> LiquidityReservation:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if amount <= 0:
            raise ValueError("amount must be positive")

        reservation = LiquidityReservation(
            account_id=account_id,
            deal_id=deal_id,
            asset=asset,
            amount=amount,
            status=LiquidityReservationStatus.ACTIVE.value,
            reference=reference,
            description=description,
        )
        self._session.add(reservation)
        await self._session.flush()
        return reservation

    async def get_reservation(
        self,
        reservation_id: uuid.UUID,
    ) -> LiquidityReservation | None:
        result = await self._session.execute(
            select(LiquidityReservation).where(LiquidityReservation.id == reservation_id)
        )
        return result.scalar_one_or_none()

    async def release_reservation(
        self,
        reservation_id: uuid.UUID,
    ) -> LiquidityReservation | None:
        result = await self._session.execute(
            select(LiquidityReservation)
            .where(LiquidityReservation.id == reservation_id)
            .with_for_update()
        )
        reservation = result.scalar_one_or_none()
        if reservation is None:
            return None
        if reservation.status != LiquidityReservationStatus.ACTIVE.value:
            raise ValueError(f"Reservation is not active: {reservation.status}")

        reservation.status = LiquidityReservationStatus.RELEASED.value
        reservation.released_at = datetime.now(timezone.utc)
        await self._session.flush()
        return reservation

    async def sum_active_reservations(self, account_id: uuid.UUID) -> Decimal:
        result = await self._session.execute(
            select(func.coalesce(func.sum(LiquidityReservation.amount), 0)).where(
                LiquidityReservation.account_id == account_id,
                LiquidityReservation.status == LiquidityReservationStatus.ACTIVE.value,
            )
        )
        return Decimal(result.scalar_one())

    async def sum_completed_inbound(self, account_id: uuid.UUID) -> Decimal:
        result = await self._session.execute(
            select(func.coalesce(func.sum(TreasuryTransfer.amount), 0)).where(
                TreasuryTransfer.to_account_id == account_id,
                TreasuryTransfer.status == TreasuryTransferStatus.COMPLETED.value,
            )
        )
        return Decimal(result.scalar_one())

    async def sum_completed_outbound(self, account_id: uuid.UUID) -> Decimal:
        result = await self._session.execute(
            select(func.coalesce(func.sum(TreasuryTransfer.amount), 0)).where(
                TreasuryTransfer.from_account_id == account_id,
                TreasuryTransfer.status == TreasuryTransferStatus.COMPLETED.value,
            )
        )
        return Decimal(result.scalar_one())

    async def list_transfers_for_account(
        self,
        account_id: uuid.UUID,
        *,
        limit: int = 200,
    ) -> list[TreasuryTransfer]:
        result = await self._session.execute(
            select(TreasuryTransfer)
            .where(
                (TreasuryTransfer.from_account_id == account_id)
                | (TreasuryTransfer.to_account_id == account_id)
            )
            .order_by(TreasuryTransfer.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
