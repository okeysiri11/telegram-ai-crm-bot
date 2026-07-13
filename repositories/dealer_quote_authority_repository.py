# Dealer Quote Authority Engine v1 repositories.

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.dealer_quote_authority_engine import (
    MarketAlert,
    QuoteDeviation,
    ReferenceMarketQuote,
)


class ReferenceMarketQuoteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        source_code: str,
        pair: str,
        bid: Decimal,
        ask: Decimal,
        mid: Decimal,
        captured_at: datetime,
        payload: dict | None = None,
    ) -> ReferenceMarketQuote:
        row = ReferenceMarketQuote(
            source_code=source_code,
            pair=pair,
            bid=bid,
            ask=ask,
            mid=mid,
            captured_at=captured_at,
            payload=payload,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def latest_by_source_pair(
        self,
        source_code: str,
        pair: str,
    ) -> ReferenceMarketQuote | None:
        result = await self._session.execute(
            select(ReferenceMarketQuote)
            .where(
                ReferenceMarketQuote.source_code == source_code,
                ReferenceMarketQuote.pair == pair,
            )
            .order_by(ReferenceMarketQuote.captured_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def latest_all(self, *, limit: int = 200) -> list[ReferenceMarketQuote]:
        result = await self._session.execute(
            select(ReferenceMarketQuote)
            .order_by(ReferenceMarketQuote.captured_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class QuoteDeviationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        pair: str,
        source_code: str,
        dealer_mid: Decimal,
        reference_mid: Decimal,
        deviation_abs: Decimal,
        deviation_pct: Decimal,
        calculated_at: datetime,
        dealer_sheet_id: uuid.UUID | None = None,
    ) -> QuoteDeviation:
        row = QuoteDeviation(
            pair=pair,
            source_code=source_code,
            dealer_mid=dealer_mid,
            reference_mid=reference_mid,
            deviation_abs=deviation_abs,
            deviation_pct=deviation_pct,
            calculated_at=calculated_at,
            dealer_sheet_id=dealer_sheet_id,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def latest_for_pair(self, pair: str, *, limit: int = 20) -> list[QuoteDeviation]:
        result = await self._session.execute(
            select(QuoteDeviation)
            .where(QuoteDeviation.pair == pair)
            .order_by(QuoteDeviation.calculated_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class MarketAlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        alert_type: str,
        severity: str,
        pair: str,
        source_code: str,
        message: str,
        deviation_pct: Decimal | None = None,
        payload: dict | None = None,
    ) -> MarketAlert:
        row = MarketAlert(
            alert_type=alert_type,
            severity=severity,
            pair=pair,
            source_code=source_code,
            message=message,
            deviation_pct=deviation_pct,
            payload=payload,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_unresolved(self, *, limit: int = 50) -> list[MarketAlert]:
        result = await self._session.execute(
            select(MarketAlert)
            .where(MarketAlert.resolved_at.is_(None))
            .order_by(MarketAlert.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def resolve_stale(self, *, resolved_at: datetime, pair: str | None = None) -> int:
        stmt = update(MarketAlert).where(MarketAlert.resolved_at.is_(None)).values(resolved_at=resolved_at)
        if pair:
            stmt = stmt.where(MarketAlert.pair == pair)
        result = await self._session.execute(stmt)
        return int(result.rowcount or 0)
