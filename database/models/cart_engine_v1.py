# Cart and Payment Engine v1 — orders and line items.

from __future__ import annotations

import enum
import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin


class CartPaymentMethod(str, enum.Enum):
    CARD = "CARD"
    IBAN = "IBAN"
    USDT = "USDT"
    CASH = "CASH"


class CartOrderStatus(str, enum.Enum):
    CREATED = "CREATED"
    WAITING_PAYMENT = "WAITING_PAYMENT"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


CART_PAYMENT_METHODS = frozenset(m.value for m in CartPaymentMethod)
CART_ORDER_STATUSES = frozenset(s.value for s in CartOrderStatus)


class CartEngineV1Order(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cart_engine_v1_orders"
    __table_args__ = (
        Index("ix_cart_engine_v1_orders_user", "user_id"),
        Index("ix_cart_engine_v1_orders_vertical", "vertical"),
        Index("ix_cart_engine_v1_orders_status", "status"),
        Index("ix_cart_engine_v1_orders_payment_method", "payment_method"),
        Index("ix_cart_engine_v1_orders_created", "created_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    vertical: Mapped[str] = mapped_column(String(50), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        default=CartOrderStatus.CREATED.value,
        nullable=False,
    )
    payment_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)


class CartEngineV1OrderItem(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "cart_engine_v1_order_items"
    __table_args__ = (
        Index("ix_cart_engine_v1_items_order", "order_id"),
        UniqueConstraint("order_id", "service_code", name="uq_cart_engine_v1_item_service"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cart_engine_v1_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    service_code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
