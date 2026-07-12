# Liquidity Engine v1 models — pools, reservations, alerts.

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
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin

import database.models.deal  # noqa: F401 — register deal_engine_deals for FK resolution


class LiquidityLocation(str, enum.Enum):
    ODESSA = "ODESSA"
    KYIV = "KYIV"
    TBILISI = "TBILISI"
    DUBAI = "DUBAI"
    BANK = "BANK"
    TRC20 = "TRC20"
    ERC20 = "ERC20"


class LiquidityReservationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    CONSUMED = "CONSUMED"


class LiquidityAlertType(str, enum.Enum):
    LOW_LIQUIDITY = "LOW_LIQUIDITY"
    NEGATIVE_BALANCE = "NEGATIVE_BALANCE"
    POOL_LIMIT_EXCEEDED = "POOL_LIMIT_EXCEEDED"


class LiquidityPool(UUIDPrimaryKeyMixin, Base):
    """Liquidity pool — maps to logical table liquidity_pools."""

    __tablename__ = "liquidity_v1_pools"
    __table_args__ = (
        CheckConstraint("available_amount >= 0", name="ck_liquidity_v1_pools_available"),
        CheckConstraint("reserved_amount >= 0", name="ck_liquidity_v1_pools_reserved"),
        UniqueConstraint("asset", "location", name="uq_liquidity_v1_pools_asset_location"),
        Index("ix_liquidity_v1_pools_asset", "asset"),
        Index("ix_liquidity_v1_pools_location", "location"),
    )

    asset: Mapped[str] = mapped_column(String(20), nullable=False)
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    available_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal("0"),
        nullable=False,
    )
    reserved_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal("0"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    @property
    def free_amount(self) -> Decimal:
        return self.available_amount - self.reserved_amount

    def __repr__(self) -> str:
        return (
            f"<LiquidityPool id={self.id} {self.asset}@{self.location} "
            f"free={self.free_amount}>"
        )


class LiquidityReservation(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Deal liquidity reservation — maps to logical table liquidity_reservations."""

    __tablename__ = "liquidity_v1_reservations"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_liquidity_v1_reservations_amount"),
        Index("ix_liquidity_v1_reservations_deal_id", "deal_id"),
        Index("ix_liquidity_v1_reservations_pool_id", "pool_id"),
        Index("ix_liquidity_v1_reservations_status", "status"),
        Index("ix_liquidity_v1_reservations_asset", "asset"),
    )

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deal_engine_deals.id", ondelete="CASCADE"),
        nullable=False,
    )
    pool_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("liquidity_v1_pools.id", ondelete="RESTRICT"),
        nullable=False,
    )
    asset: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=LiquidityReservationStatus.ACTIVE.value,
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<LiquidityReservation id={self.id} deal={self.deal_id} "
            f"amount={self.amount} {self.asset} status={self.status}>"
        )


class LiquidityAlert(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "liquidity_v1_alerts"
    __table_args__ = (
        Index("ix_liquidity_v1_alerts_alert_type", "alert_type"),
        Index("ix_liquidity_v1_alerts_asset", "asset"),
        Index("ix_liquidity_v1_alerts_is_resolved", "is_resolved"),
    )

    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    pool_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("liquidity_v1_pools.id", ondelete="SET NULL"),
        nullable=True,
    )
    asset: Mapped[str | None] = mapped_column(String(20), nullable=True)
    deal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deal_engine_deals.id", ondelete="SET NULL"),
        nullable=True,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<LiquidityAlert id={self.id} type={self.alert_type} resolved={self.is_resolved}>"
