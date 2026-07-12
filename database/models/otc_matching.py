# OTC Matching Engine v1 — orders, quotes, matches, routes, fill history.

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin

import database.models.deal  # noqa: F401
import database.models.partner_engine  # noqa: F401


class OtcOrderType(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class OtcExecutionMode(str, enum.Enum):
    MANUAL = "MANUAL"
    SEMI_AUTO = "SEMI_AUTO"
    AUTO = "AUTO"


class OtcMatchingStrategy(str, enum.Enum):
    BEST_PRICE = "BEST_PRICE"
    BEST_LIQUIDITY = "BEST_LIQUIDITY"
    LOWEST_RISK = "LOWEST_RISK"
    FASTEST_EXECUTION = "FASTEST_EXECUTION"


class OtcOrderStatus(str, enum.Enum):
    OPEN = "OPEN"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"


class OtcQuoteStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"


class OtcMatchStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class OtcRouteStatus(str, enum.Enum):
    PLANNED = "PLANNED"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class OtcOrder(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "otc_v1_orders"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_otc_v1_orders_amount"),
        CheckConstraint("filled_amount >= 0", name="ck_otc_v1_orders_filled"),
        CheckConstraint("remaining_amount >= 0", name="ck_otc_v1_orders_remaining"),
        Index("ix_otc_v1_orders_status", "status"),
        Index("ix_otc_v1_orders_order_type", "order_type"),
        Index("ix_otc_v1_orders_asset", "asset"),
        Index("ix_otc_v1_orders_deal_id", "deal_id"),
        Index("ix_otc_v1_orders_partner_id", "partner_id"),
    )

    deal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deal_engine_deals.id", ondelete="SET NULL"),
        nullable=True,
    )
    partner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_engine_partners.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    order_type: Mapped[str] = mapped_column(String(10), nullable=False)
    asset: Mapped[str] = mapped_column(String(20), nullable=False)
    quote_asset: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    filled_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 8),
        default=Decimal("0"),
        nullable=False,
    )
    remaining_amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    price_limit: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)
    execution_mode: Mapped[str] = mapped_column(
        String(20),
        default=OtcExecutionMode.MANUAL.value,
        nullable=False,
    )
    matching_strategy: Mapped[str] = mapped_column(
        String(30),
        default=OtcMatchingStrategy.BEST_PRICE.value,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=OtcOrderStatus.OPEN.value,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<OtcOrder id={self.id} {self.order_type} "
            f"{self.amount} {self.asset} status={self.status}>"
        )


class OtcQuote(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "otc_v1_quotes"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_otc_v1_quotes_amount"),
        CheckConstraint("price > 0", name="ck_otc_v1_quotes_price"),
        Index("ix_otc_v1_quotes_order_id", "order_id"),
        Index("ix_otc_v1_quotes_partner_id", "partner_id"),
        Index("ix_otc_v1_quotes_status", "status"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("otc_v1_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_engine_partners.id", ondelete="RESTRICT"),
        nullable=False,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    available_amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=OtcQuoteStatus.ACTIVE.value,
        nullable=False,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<OtcQuote id={self.id} order={self.order_id} "
            f"price={self.price} amount={self.amount}>"
        )


class OtcMatch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "otc_v1_matches"
    __table_args__ = (
        CheckConstraint("matched_amount > 0", name="ck_otc_v1_matches_amount"),
        CheckConstraint("matched_price > 0", name="ck_otc_v1_matches_price"),
        Index("ix_otc_v1_matches_order_id", "order_id"),
        Index("ix_otc_v1_matches_quote_id", "quote_id"),
        Index("ix_otc_v1_matches_partner_id", "partner_id"),
        Index("ix_otc_v1_matches_status", "status"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("otc_v1_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    quote_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("otc_v1_quotes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_engine_partners.id", ondelete="RESTRICT"),
        nullable=False,
    )
    matched_amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    matched_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=OtcMatchStatus.PENDING.value,
        nullable=False,
    )
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    approved_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<OtcMatch id={self.id} order={self.order_id} "
            f"amount={self.matched_amount} status={self.status}>"
        )


class OtcExecutionRoute(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "otc_v1_execution_routes"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_otc_v1_execution_routes_amount"),
        Index("ix_otc_v1_execution_routes_order_id", "order_id"),
        Index("ix_otc_v1_execution_routes_partner_id", "partner_id"),
        Index("ix_otc_v1_execution_routes_status", "status"),
        Index("ix_otc_v1_execution_routes_step_order", "step_order"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("otc_v1_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    match_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("otc_v1_matches.id", ondelete="SET NULL"),
        nullable=True,
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_engine_partners.id", ondelete="RESTRICT"),
        nullable=False,
    )
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=OtcRouteStatus.PLANNED.value,
        nullable=False,
    )
    liquidity_score: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 4),
        nullable=True,
    )
    risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<OtcExecutionRoute id={self.id} order={self.order_id} "
            f"step={self.step_order} amount={self.amount}>"
        )


class OtcFillHistory(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "otc_v1_fill_history"
    __table_args__ = (
        CheckConstraint("fill_amount > 0", name="ck_otc_v1_fill_history_amount"),
        Index("ix_otc_v1_fill_history_order_id", "order_id"),
        Index("ix_otc_v1_fill_history_match_id", "match_id"),
        Index("ix_otc_v1_fill_history_route_id", "route_id"),
        Index("ix_otc_v1_fill_history_partner_id", "partner_id"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("otc_v1_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    match_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("otc_v1_matches.id", ondelete="SET NULL"),
        nullable=True,
    )
    route_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("otc_v1_execution_routes.id", ondelete="SET NULL"),
        nullable=True,
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_engine_partners.id", ondelete="RESTRICT"),
        nullable=False,
    )
    fill_amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    fill_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    filled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<OtcFillHistory id={self.id} order={self.order_id} "
            f"fill={self.fill_amount}@{self.fill_price}>"
        )
