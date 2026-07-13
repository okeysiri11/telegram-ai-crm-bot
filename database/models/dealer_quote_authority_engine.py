# Dealer Quote Authority Engine v1 — reference quotes, deviations, market alerts.

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin


class ReferenceSourceCode(str, enum.Enum):
    NBU = "NBU"
    PRIVATBANK = "PRIVATBANK"
    MONOBANK = "MONOBANK"
    UKRSIBBANK = "UKRSIBBANK"
    MTB_BANK = "MTB_BANK"
    OSCHADBANK = "OSCHADBANK"
    WHITEBIT = "WHITEBIT"
    OKX = "OKX"
    BYBIT = "BYBIT"
    TRADINGVIEW = "TRADINGVIEW"


class QuotePair(str, enum.Enum):
    USD_UAH = "USD_UAH"
    EUR_UAH = "EUR_UAH"
    USDT_UAH = "USDT_UAH"


class AlertSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


REFERENCE_SOURCE_CODES = frozenset(s.value for s in ReferenceSourceCode)
QUOTE_PAIRS = frozenset(p.value for p in QuotePair)


class ReferenceMarketQuote(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "dealer_quote_authority_v1_reference_quotes"
    __table_args__ = (
        Index("ix_dqa_ref_source", "source_code"),
        Index("ix_dqa_ref_pair", "pair"),
        Index("ix_dqa_ref_captured", "captured_at"),
    )

    source_code: Mapped[str] = mapped_column(String(32), nullable=False)
    pair: Mapped[str] = mapped_column(String(32), nullable=False)
    bid: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    ask: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    mid: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<ReferenceMarketQuote source={self.source_code} pair={self.pair}>"


class QuoteDeviation(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "dealer_quote_authority_v1_deviations"
    __table_args__ = (
        Index("ix_dqa_dev_pair", "pair"),
        Index("ix_dqa_dev_source", "source_code"),
        Index("ix_dqa_dev_calculated", "calculated_at"),
    )

    pair: Mapped[str] = mapped_column(String(32), nullable=False)
    source_code: Mapped[str] = mapped_column(String(32), nullable=False)
    dealer_mid: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    reference_mid: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    deviation_abs: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    deviation_pct: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dealer_sheet_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_treasury_v1_rate_sheets.id", ondelete="SET NULL"),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<QuoteDeviation pair={self.pair} source={self.source_code} pct={self.deviation_pct}>"


class MarketAlert(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "dealer_quote_authority_v1_market_alerts"
    __table_args__ = (
        Index("ix_dqa_alert_severity", "severity"),
        Index("ix_dqa_alert_resolved", "resolved_at"),
        Index("ix_dqa_alert_pair", "pair"),
    )

    alert_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    pair: Mapped[str] = mapped_column(String(32), nullable=False)
    source_code: Mapped[str] = mapped_column(String(32), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    deviation_pct: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<MarketAlert pair={self.pair} severity={self.severity}>"
