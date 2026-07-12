# Market Data Engine v1 models — sources, quotes, orderbooks, spreads, snapshots.

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin

SUPPORTED_ASSETS = frozenset({
    "USD", "EUR", "USDT", "BTC", "ETH", "AED", "PLN", "GEL", "UAH",
})

MARKET_PAIRS: tuple[tuple[str, str], ...] = (
    ("USD", "UAH"),
    ("USD", "EUR"),
    ("EUR", "AED"),
    ("USDT", "USD"),
    ("BTC", "USDT"),
)


class MarketSourceCode(str, enum.Enum):
    BINANCE = "BINANCE"
    BYBIT = "BYBIT"
    WHITEBIT = "WHITEBIT"
    MANUAL = "MANUAL"
    FX = "FX"
    PRECIOUS_METALS = "PRECIOUS_METALS"


class MarketSourceType(str, enum.Enum):
    EXCHANGE = "EXCHANGE"
    MANUAL = "MANUAL"
    FX = "FX"
    METALS = "METALS"


class MarketSnapshotType(str, enum.Enum):
    FULL = "FULL"
    QUOTE = "QUOTE"
    ORDERBOOK = "ORDERBOOK"


class MarketSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "market_v1_sources"
    __table_args__ = (
        Index("ix_market_v1_sources_source_code", "source_code"),
        Index("ix_market_v1_sources_is_active", "is_active"),
        Index("ix_market_v1_sources_priority", "priority"),
    )

    source_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_failure_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<MarketSource code={self.source_code} active={self.is_active}>"


class MarketQuote(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "market_v1_quotes"
    __table_args__ = (
        CheckConstraint("bid >= 0", name="ck_market_v1_quotes_bid"),
        CheckConstraint("ask >= 0", name="ck_market_v1_quotes_ask"),
        CheckConstraint("last >= 0", name="ck_market_v1_quotes_last"),
        UniqueConstraint("source_id", "asset", name="uq_market_v1_quotes_source_asset"),
        Index("ix_market_v1_quotes_asset", "asset"),
        Index("ix_market_v1_quotes_quoted_at", "quoted_at"),
    )

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("market_v1_sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    asset: Mapped[str] = mapped_column(String(20), nullable=False)
    quote_symbol: Mapped[str | None] = mapped_column(String(40), nullable=True)
    bid: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    ask: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    last: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    spread: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    volume_24h: Mapped[Decimal | None] = mapped_column(Numeric(24, 8), nullable=True)
    quoted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<MarketQuote asset={self.asset} bid={self.bid} ask={self.ask} "
            f"last={self.last}>"
        )


class MarketOrderbook(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "market_v1_orderbooks"
    __table_args__ = (
        Index("ix_market_v1_orderbooks_source_id", "source_id"),
        Index("ix_market_v1_orderbooks_asset", "asset"),
        Index("ix_market_v1_orderbooks_captured_at", "captured_at"),
    )

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("market_v1_sources.id", ondelete="CASCADE"),
        nullable=False,
    )
    asset: Mapped[str] = mapped_column(String(20), nullable=False)
    bids: Mapped[list] = mapped_column(JSONB, nullable=False)
    asks: Mapped[list] = mapped_column(JSONB, nullable=False)
    depth: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<MarketOrderbook asset={self.asset} depth={self.depth}>"


class MarketSpread(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "market_v1_spreads"
    __table_args__ = (
        Index("ix_market_v1_spreads_asset", "asset"),
        Index("ix_market_v1_spreads_source_id", "source_id"),
        Index("ix_market_v1_spreads_calculated_at", "calculated_at"),
    )

    asset: Mapped[str] = mapped_column(String(20), nullable=False)
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("market_v1_sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    best_bid: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    best_ask: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    mid_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    spread_abs: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    spread_pct: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<MarketSpread asset={self.asset} spread_pct={self.spread_pct} "
            f"mid={self.mid_price}>"
        )


class MarketSnapshot(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "market_v1_snapshots"
    __table_args__ = (
        Index("ix_market_v1_snapshots_snapshot_type", "snapshot_type"),
        Index("ix_market_v1_snapshots_asset", "asset"),
        Index("ix_market_v1_snapshots_captured_at", "captured_at"),
    )

    snapshot_type: Mapped[str] = mapped_column(String(20), nullable=False)
    asset: Mapped[str | None] = mapped_column(String(20), nullable=True)
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("market_v1_sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<MarketSnapshot type={self.snapshot_type} asset={self.asset}>"
