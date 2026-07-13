# Automotive Treasury Engine v1 — dealer FX rates from Telegram channel.

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin


class DealerRateField(str, enum.Enum):
    USD_BUY = "USD_BUY"
    USD_SELL = "USD_SELL"
    EUR_BUY = "EUR_BUY"
    EUR_SELL = "EUR_SELL"
    USDT_BUY = "USDT_BUY"
    USDT_SELL = "USDT_SELL"
    USD_WHITE_PREMIUM = "USD_WHITE_PREMIUM"
    USD_BLUE_PREMIUM = "USD_BLUE_PREMIUM"


DEALER_RATE_FIELDS = frozenset(f.value for f in DealerRateField)
AUTOMOTIVE_TREASURY_CURRENCIES = frozenset({"UAH", "USD", "EUR", "USDT"})


class AutomotiveDealerRateSheet(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Active dealer rate sheet — valid until replaced by a new channel update."""

    __tablename__ = "automotive_treasury_v1_rate_sheets"
    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_automotive_treasury_v1_rate_sheets_tenant"),
        Index("ix_automotive_treasury_v1_rate_sheets_tenant", "tenant_id"),
        Index("ix_automotive_treasury_v1_rate_sheets_active", "is_active"),
        Index("ix_automotive_treasury_v1_rate_sheets_updated", "source_updated_at"),
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    usd_buy: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    usd_sell: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    eur_buy: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    eur_sell: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    usdt_buy: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    usdt_sell: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    eurusd_buy: Mapped[Decimal | None] = mapped_column(Numeric(20, 6), nullable=True)
    eurusd_sell: Mapped[Decimal | None] = mapped_column(Numeric(20, 6), nullable=True)
    usdt_buy_markup_percent: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    usdt_sell_markup_percent: Mapped[Decimal | None] = mapped_column(Numeric(12, 6), nullable=True)
    usd_white_premium: Mapped[Decimal | None] = mapped_column(Numeric(20, 6), nullable=True)
    usd_blue_premium: Mapped[Decimal | None] = mapped_column(Numeric(20, 6), nullable=True)

    source_authority: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_channel_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_by_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    def __repr__(self) -> str:
        return f"<AutomotiveDealerRateSheet tenant={self.tenant_id} active={self.is_active}>"


class AutomotiveDealerRateHistory(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "automotive_treasury_v1_rate_history"
    __table_args__ = (
        Index("ix_automotive_treasury_v1_history_tenant", "tenant_id"),
        Index("ix_automotive_treasury_v1_history_updated", "source_updated_at"),
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
    )
    rates: Mapped[dict] = mapped_column(JSONB, nullable=False)
    source_channel_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_by_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    def __repr__(self) -> str:
        return f"<AutomotiveDealerRateHistory tenant={self.tenant_id}>"
