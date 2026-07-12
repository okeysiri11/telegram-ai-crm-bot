# Pricing Engine v1 models — price sources, spreads, partner/manager pricing.

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

import database.models.partner_engine  # noqa: F401 — register partner_engine_partners


class PriceSourceName(str, enum.Enum):
    BINANCE = "BINANCE"
    WHITEBIT = "WHITEBIT"
    BYBIT = "BYBIT"
    MANUAL = "MANUAL"
    AUTO_MARKET = "AUTO_MARKET"
    CUSTOM = "CUSTOM"


class SpreadRuleType(str, enum.Enum):
    FIXED = "FIXED"
    PERCENTAGE = "PERCENTAGE"


class PriceSource(UUIDPrimaryKeyMixin, Base):
    """Market price source — maps to logical table price_sources."""

    __tablename__ = "pricing_v1_price_sources"
    __table_args__ = (
        CheckConstraint("bid_price > 0", name="ck_pricing_v1_price_sources_bid"),
        CheckConstraint("ask_price > 0", name="ck_pricing_v1_price_sources_ask"),
        UniqueConstraint("source_name", "asset", name="uq_pricing_v1_price_sources_name_asset"),
        Index("ix_pricing_v1_price_sources_asset", "asset"),
        Index("ix_pricing_v1_price_sources_source_name", "source_name"),
    )

    source_name: Mapped[str] = mapped_column(String(100), nullable=False)
    asset: Mapped[str] = mapped_column(String(20), nullable=False)
    bid_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    ask_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<PriceSource id={self.id} {self.source_name} "
            f"{self.asset} bid={self.bid_price} ask={self.ask_price}>"
        )


class SpreadRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Spread rule — maps to logical table spread_rules."""

    __tablename__ = "pricing_v1_spread_rules"
    __table_args__ = (
        CheckConstraint("value >= 0", name="ck_pricing_v1_spread_rules_value"),
        Index("ix_pricing_v1_spread_rules_asset", "asset"),
        Index("ix_pricing_v1_spread_rules_priority", "priority"),
    )

    asset: Mapped[str] = mapped_column(String(20), nullable=False)
    spread_type: Mapped[str] = mapped_column(String(20), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<SpreadRule id={self.id} asset={self.asset} "
            f"type={self.spread_type} value={self.value}>"
        )


class PartnerPricing(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Partner-specific pricing — maps to logical table partner_pricing."""

    __tablename__ = "pricing_v1_partner_pricing"
    __table_args__ = (
        CheckConstraint("custom_spread >= 0", name="ck_pricing_v1_partner_pricing_spread"),
        UniqueConstraint("partner_id", "asset", name="uq_pricing_v1_partner_pricing_partner_asset"),
        Index("ix_pricing_v1_partner_pricing_partner_id", "partner_id"),
        Index("ix_pricing_v1_partner_pricing_asset", "asset"),
    )

    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_engine_partners.id", ondelete="CASCADE"),
        nullable=False,
    )
    asset: Mapped[str] = mapped_column(String(20), nullable=False)
    custom_spread: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)

    def __repr__(self) -> str:
        return (
            f"<PartnerPricing partner={self.partner_id} "
            f"asset={self.asset} spread={self.custom_spread}>"
        )


class ManagerPricing(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Manager-specific margin — maps to logical table manager_pricing."""

    __tablename__ = "pricing_v1_manager_pricing"
    __table_args__ = (
        CheckConstraint("custom_margin >= 0", name="ck_pricing_v1_manager_pricing_margin"),
        UniqueConstraint("manager_id", "asset", name="uq_pricing_v1_manager_pricing_manager_asset"),
        Index("ix_pricing_v1_manager_pricing_manager_id", "manager_id"),
        Index("ix_pricing_v1_manager_pricing_asset", "asset"),
    )

    manager_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    asset: Mapped[str] = mapped_column(String(20), nullable=False)
    custom_margin: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)

    def __repr__(self) -> str:
        return (
            f"<ManagerPricing manager={self.manager_id} "
            f"asset={self.asset} margin={self.custom_margin}>"
        )
