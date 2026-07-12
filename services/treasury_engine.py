# Treasury Engine — fund reservations, transfers, and balance reconciliation.

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from database.models.treasury import (
    LiquidityReservation,
    LiquidityReservationStatus,
    TreasuryAccount,
    TreasuryAccountStatus,
    TreasuryTransfer,
    TreasuryTransferStatus,
    TreasuryTransferType,
)
from database.session import get_session
from repositories.treasury_repository import TreasuryRepository


class TreasuryEngineError(Exception):
    pass


class InsufficientFundsError(TreasuryEngineError):
    pass


class TreasuryEngine:
    @staticmethod
    async def create_account(
        *,
        code: str,
        name: str,
        asset: str,
        account_type: str = "OPERATING",
        initial_balance: Decimal = Decimal("0"),
    ) -> TreasuryAccount:
        async with get_session() as session:
            repo = TreasuryRepository(session)
            return await repo.create_account(
                code=code,
                name=name,
                asset=asset,
                account_type=account_type,
                balance=initial_balance,
            )

    @staticmethod
    async def get_account(account_id: uuid.UUID) -> TreasuryAccount | None:
        async with get_session() as session:
            return await TreasuryRepository(session).get_account(account_id)

    @staticmethod
    async def reserve_funds(
        *,
        account_id: uuid.UUID,
        amount: Decimal,
        deal_id: uuid.UUID | None = None,
        reference: str | None = None,
        description: str | None = None,
    ) -> LiquidityReservation:
        if amount <= 0:
            raise ValueError("amount must be positive")

        async with get_session() as session:
            repo = TreasuryRepository(session)
            account = await repo.get_account_for_update(account_id)
            if account is None:
                raise TreasuryEngineError(f"Account not found: {account_id}")
            if account.status != TreasuryAccountStatus.ACTIVE.value:
                raise TreasuryEngineError(f"Account is not active: {account.status}")

            available = account.balance - account.reserved_balance
            if available < amount:
                raise InsufficientFundsError(
                    f"Insufficient available balance: {available} < {amount}"
                )

            reservation = await repo.create_reservation(
                account_id=account_id,
                asset=account.asset,
                amount=amount,
                deal_id=deal_id,
                reference=reference,
                description=description,
            )
            account.reserved_balance += amount
            await session.flush()
            return reservation

    @staticmethod
    async def release_reserve(reservation_id: uuid.UUID) -> LiquidityReservation:
        async with get_session() as session:
            repo = TreasuryRepository(session)
            reservation = await repo.get_reservation(reservation_id)
            if reservation is None:
                raise TreasuryEngineError(f"Reservation not found: {reservation_id}")

            account = await repo.get_account_for_update(reservation.account_id)
            if account is None:
                raise TreasuryEngineError(
                    f"Account not found: {reservation.account_id}"
                )

            released = await repo.release_reservation(reservation_id)
            if released is None:
                raise TreasuryEngineError(f"Reservation not found: {reservation_id}")

            account.reserved_balance = max(
                Decimal("0"),
                account.reserved_balance - released.amount,
            )
            await session.flush()
            return released

    @staticmethod
    async def internal_transfer(
        *,
        from_account_id: uuid.UUID,
        to_account_id: uuid.UUID,
        amount: Decimal,
        deal_id: uuid.UUID | None = None,
        reference: str | None = None,
        description: str | None = None,
    ) -> TreasuryTransfer:
        if amount <= 0:
            raise ValueError("amount must be positive")
        if from_account_id == to_account_id:
            raise ValueError("from_account_id and to_account_id must differ")

        async with get_session() as session:
            repo = TreasuryRepository(session)
            first_id, second_id = sorted(
                (from_account_id, to_account_id),
                key=lambda value: str(value),
            )
            first = await repo.get_account_for_update(first_id)
            second = await repo.get_account_for_update(second_id)
            if first is None or second is None:
                raise TreasuryEngineError("One or both accounts not found")

            from_account = first if first.id == from_account_id else second
            to_account = second if second.id == to_account_id else first

            if from_account.status != TreasuryAccountStatus.ACTIVE.value:
                raise TreasuryEngineError(
                    f"Source account is not active: {from_account.status}"
                )
            if to_account.status != TreasuryAccountStatus.ACTIVE.value:
                raise TreasuryEngineError(
                    f"Destination account is not active: {to_account.status}"
                )
            if from_account.asset != to_account.asset:
                raise TreasuryEngineError(
                    f"Asset mismatch: {from_account.asset} != {to_account.asset}"
                )

            available = from_account.balance - from_account.reserved_balance
            if available < amount:
                raise InsufficientFundsError(
                    f"Insufficient available balance: {available} < {amount}"
                )

            transfer = await repo.create_transfer(
                from_account_id=from_account_id,
                to_account_id=to_account_id,
                asset=from_account.asset,
                amount=amount,
                transfer_type=TreasuryTransferType.INTERNAL.value,
                status=TreasuryTransferStatus.COMPLETED.value,
                deal_id=deal_id,
                reference=reference,
                description=description,
            )
            from_account.balance -= amount
            to_account.balance += amount
            await repo.complete_transfer(transfer.id)
            await session.flush()
            return transfer

    @staticmethod
    async def balance_reconciliation(
        account_id: uuid.UUID,
        *,
        opening_balance: Decimal = Decimal("0"),
        auto_fix: bool = False,
    ) -> dict[str, Any]:
        async with get_session() as session:
            repo = TreasuryRepository(session)
            account = await repo.get_account(account_id)
            if account is None:
                raise TreasuryEngineError(f"Account not found: {account_id}")

            inbound = await repo.sum_completed_inbound(account_id)
            outbound = await repo.sum_completed_outbound(account_id)
            computed_balance = opening_balance + inbound - outbound
            computed_reserved = await repo.sum_active_reservations(account_id)

            balance_difference = account.balance - computed_balance
            reserved_difference = account.reserved_balance - computed_reserved
            is_balanced = (
                balance_difference == 0 and reserved_difference == 0
            )

            if auto_fix and not is_balanced:
                locked = await repo.get_account_for_update(account_id)
                if locked is not None:
                    locked.balance = computed_balance
                    locked.reserved_balance = computed_reserved
                    await session.flush()
                    account = locked
                    balance_difference = Decimal("0")
                    reserved_difference = Decimal("0")
                    is_balanced = True

            return {
                "account_id": str(account_id),
                "code": account.code,
                "asset": account.asset,
                "stored_balance": account.balance,
                "computed_balance": computed_balance,
                "balance_difference": balance_difference,
                "stored_reserved": account.reserved_balance,
                "computed_reserved": computed_reserved,
                "reserved_difference": reserved_difference,
                "available_balance": account.balance - account.reserved_balance,
                "inbound_total": inbound,
                "outbound_total": outbound,
                "opening_balance": opening_balance,
                "is_balanced": is_balanced,
            }
