# Manual Payment Verification Engine v1.

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PaymentEngineMethod(str, enum.Enum):
    CARD = "CARD"
    IBAN = "IBAN"
    USDT_TRC20 = "USDT_TRC20"
    USDT_ERC20 = "USDT_ERC20"
    CASH = "CASH"


class PaymentEngineStatus(str, enum.Enum):
    CREATED = "CREATED"
    WAITING_PAYMENT = "WAITING_PAYMENT"
    PAYMENT_UPLOADED = "PAYMENT_UPLOADED"
    UNDER_REVIEW = "UNDER_REVIEW"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    REFUNDED = "REFUNDED"


PAYMENT_ENGINE_METHODS = frozenset(m.value for m in PaymentEngineMethod)
PAYMENT_ENGINE_STATUSES = frozenset(s.value for s in PaymentEngineStatus)
PAYMENT_ENGINE_PENDING_STATUSES = frozenset({
    PaymentEngineStatus.WAITING_PAYMENT.value,
    PaymentEngineStatus.PAYMENT_UPLOADED.value,
    PaymentEngineStatus.UNDER_REVIEW.value,
})


class PaymentEngineV1Payment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payment_engine_v1_payments"
    __table_args__ = (
        Index("ix_payment_engine_v1_order", "order_id"),
        Index("ix_payment_engine_v1_client", "client_id"),
        Index("ix_payment_engine_v1_status", "status"),
        Index("ix_payment_engine_v1_method", "payment_method"),
        Index("ix_payment_engine_v1_deal", "deal_id"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cart_engine_v1_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    deal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deal_engine_v1_deals.id", ondelete="SET NULL"),
        nullable=True,
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    payment_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    screenshot_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default=PaymentEngineStatus.CREATED.value,
        nullable=False,
    )
