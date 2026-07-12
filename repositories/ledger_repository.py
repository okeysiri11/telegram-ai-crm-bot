# Ledger Engine repository — PostgreSQL async data access.

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.ledger_entry import (
    LedgerAccountType,
    LedgerDirection,
    LedgerEntry,
)


def _signed_amount_column():
    return func.sum(
        case(
            (LedgerEntry.direction == LedgerDirection.CREDIT.value, LedgerEntry.amount),
            else_=-LedgerEntry.amount,
        )
    )


class LedgerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_entry(
        self,
        *,
        account_type: str,
        asset: str,
        amount: Decimal,
        direction: str,
        deal_id: uuid.UUID | None = None,
        account_id: int | None = None,
        description: str | None = None,
        **extra: Any,
    ) -> LedgerEntry:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        if direction not in {d.value for d in LedgerDirection}:
            raise ValueError(f"Invalid direction: {direction}")
        if account_type not in {a.value for a in LedgerAccountType}:
            raise ValueError(f"Invalid account_type: {account_type}")
        if amount <= 0:
            raise ValueError("amount must be positive")

        entry = LedgerEntry(
            deal_id=deal_id,
            account_type=account_type,
            account_id=account_id,
            asset=asset,
            amount=amount,
            direction=direction,
            description=description,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def get_balance(self, asset: str) -> Decimal:
        result = await self._session.execute(
            select(_signed_amount_column()).where(LedgerEntry.asset == asset)
        )
        balance = result.scalar_one_or_none()
        return Decimal(balance or 0)

    async def get_account_balance(
        self,
        account_type: str,
        account_id: int | None,
        asset: str,
    ) -> Decimal:
        stmt = select(_signed_amount_column()).where(
            LedgerEntry.account_type == account_type,
            LedgerEntry.asset == asset,
        )
        if account_id is None:
            stmt = stmt.where(LedgerEntry.account_id.is_(None))
        else:
            stmt = stmt.where(LedgerEntry.account_id == account_id)

        result = await self._session.execute(stmt)
        balance = result.scalar_one_or_none()
        return Decimal(balance or 0)

    async def list_by_deal(self, deal_id: uuid.UUID) -> list[LedgerEntry]:
        result = await self._session.execute(
            select(LedgerEntry)
            .where(LedgerEntry.deal_id == deal_id)
            .order_by(LedgerEntry.created_at.asc())
        )
        return list(result.scalars().all())
