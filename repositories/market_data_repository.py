# Market Data Engine v1 repositories — PostgreSQL async data access.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.market_data import (
    SUPPORTED_ASSETS,
    MarketOrderbook,
    MarketQuote,
    MarketSnapshot,
    MarketSource,
    MarketSourceCode,
    MarketSourceType,
    MarketSpread,
    MarketSnapshotType,
)


class MarketSourceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        source_code: str,
        source_type: str,
        name: str,
        base_url: str | None = None,
        priority: int = 100,
        is_active: bool = True,
        config: dict | None = None,
        **extra: Any,
    ) -> MarketSource:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if source_code not in {c.value for c in MarketSourceCode}:
            raise ValueError(f"Invalid source_code: {source_code}")
        if source_type not in {t.value for t in MarketSourceType}:
            raise ValueError(f"Invalid source_type: {source_type}")

        source = MarketSource(
            source_code=source_code,
            source_type=source_type,
            name=name,
            base_url=base_url,
            priority=priority,
            is_active=is_active,
            config=config,
        )
        self._session.add(source)
        await self._session.flush()
        return source

    async def get_by_code(self, source_code: str) -> MarketSource | None:
        result = await self._session.execute(
            select(MarketSource).where(MarketSource.source_code == source_code)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, source_id: uuid.UUID) -> MarketSource | None:
        result = await self._session.execute(
            select(MarketSource).where(MarketSource.id == source_id)
        )
        return result.scalar_one_or_none()

    async def list_active(self) -> list[MarketSource]:
        result = await self._session.execute(
            select(MarketSource)
            .where(MarketSource.is_active.is_(True))
            .order_by(MarketSource.priority.asc())
        )
        return list(result.scalars().all())

    async def mark_success(self, source_id: uuid.UUID) -> MarketSource | None:
        source = await self.get_by_id(source_id)
        if source is None:
            return None
        source.last_success_at = datetime.now(timezone.utc)
        source.failure_count = 0
        await self._session.flush()
        return source

    async def mark_failure(self, source_id: uuid.UUID) -> MarketSource | None:
        source = await self.get_by_id(source_id)
        if source is None:
            return None
        source.last_failure_at = datetime.now(timezone.utc)
        source.failure_count += 1
        await self._session.flush()
        return source


class MarketQuoteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        *,
        source_id: uuid.UUID,
        asset: str,
        bid: Decimal,
        ask: Decimal,
        last: Decimal,
        spread: Decimal,
        volume_24h: Decimal | None = None,
        quote_symbol: str | None = None,
        quoted_at: datetime | None = None,
    ) -> MarketQuote:
        if asset not in SUPPORTED_ASSETS:
            raise ValueError(f"Unsupported asset: {asset}")

        result = await self._session.execute(
            select(MarketQuote).where(
                MarketQuote.source_id == source_id,
                MarketQuote.asset == asset,
            )
        )
        quote = result.scalar_one_or_none()
        now = quoted_at or datetime.now(timezone.utc)

        if quote is None:
            quote = MarketQuote(
                source_id=source_id,
                asset=asset,
                quote_symbol=quote_symbol,
                bid=bid,
                ask=ask,
                last=last,
                spread=spread,
                volume_24h=volume_24h,
                quoted_at=now,
            )
            self._session.add(quote)
        else:
            quote.quote_symbol = quote_symbol
            quote.bid = bid
            quote.ask = ask
            quote.last = last
            quote.spread = spread
            quote.volume_24h = volume_24h
            quote.quoted_at = now

        await self._session.flush()
        return quote

    async def get_by_source_asset(
        self,
        source_id: uuid.UUID,
        asset: str,
    ) -> MarketQuote | None:
        result = await self._session.execute(
            select(MarketQuote).where(
                MarketQuote.source_id == source_id,
                MarketQuote.asset == asset,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_asset(self, asset: str) -> list[MarketQuote]:
        result = await self._session.execute(
            select(MarketQuote)
            .where(MarketQuote.asset == asset)
            .order_by(MarketQuote.quoted_at.desc())
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[MarketQuote]:
        result = await self._session.execute(
            select(MarketQuote).order_by(MarketQuote.asset.asc(), MarketQuote.quoted_at.desc())
        )
        return list(result.scalars().all())

    async def best_bid(self, asset: str) -> MarketQuote | None:
        quotes = await self.list_by_asset(asset)
        if not quotes:
            return None
        return max(quotes, key=lambda q: q.bid)

    async def best_ask(self, asset: str) -> MarketQuote | None:
        quotes = await self.list_by_asset(asset)
        if not quotes:
            return None
        return min(quotes, key=lambda q: q.ask)


class MarketOrderbookRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        source_id: uuid.UUID,
        asset: str,
        bids: list,
        asks: list,
        depth: int = 5,
        captured_at: datetime | None = None,
        **extra: Any,
    ) -> MarketOrderbook:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        book = MarketOrderbook(
            source_id=source_id,
            asset=asset,
            bids=bids,
            asks=asks,
            depth=depth,
            captured_at=captured_at or datetime.now(timezone.utc),
        )
        self._session.add(book)
        await self._session.flush()
        return book

    async def latest(self, source_id: uuid.UUID, asset: str) -> MarketOrderbook | None:
        result = await self._session.execute(
            select(MarketOrderbook)
            .where(
                MarketOrderbook.source_id == source_id,
                MarketOrderbook.asset == asset,
            )
            .order_by(MarketOrderbook.captured_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class MarketSpreadRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        asset: str,
        best_bid: Decimal,
        best_ask: Decimal,
        mid_price: Decimal,
        spread_abs: Decimal,
        spread_pct: Decimal,
        source_id: uuid.UUID | None = None,
        calculated_at: datetime | None = None,
        **extra: Any,
    ) -> MarketSpread:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        spread = MarketSpread(
            asset=asset,
            source_id=source_id,
            best_bid=best_bid,
            best_ask=best_ask,
            mid_price=mid_price,
            spread_abs=spread_abs,
            spread_pct=spread_pct,
            calculated_at=calculated_at or datetime.now(timezone.utc),
        )
        self._session.add(spread)
        await self._session.flush()
        return spread

    async def latest_for_asset(self, asset: str) -> MarketSpread | None:
        result = await self._session.execute(
            select(MarketSpread)
            .where(MarketSpread.asset == asset, MarketSpread.source_id.is_(None))
            .order_by(MarketSpread.calculated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class MarketSnapshotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        snapshot_type: str,
        payload: dict,
        asset: str | None = None,
        source_id: uuid.UUID | None = None,
        captured_at: datetime | None = None,
        **extra: Any,
    ) -> MarketSnapshot:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if snapshot_type not in {t.value for t in MarketSnapshotType}:
            raise ValueError(f"Invalid snapshot_type: {snapshot_type}")

        snapshot = MarketSnapshot(
            snapshot_type=snapshot_type,
            asset=asset,
            source_id=source_id,
            payload=payload,
            captured_at=captured_at or datetime.now(timezone.utc),
        )
        self._session.add(snapshot)
        await self._session.flush()
        return snapshot
