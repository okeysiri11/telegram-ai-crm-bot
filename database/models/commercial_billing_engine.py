# Commercial Billing Engine v1 — payments, receipts, subscription history, billing events.

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

import database.models.tenant_billing_engine  # noqa: F401


class PricingModel(str, enum.Enum):
    SUBSCRIPTION = "SUBSCRIPTION"
    PER_LEAD = "PER_LEAD"
    REVENUE_SHARE = "REVENUE_SHARE"
    HYBRID = "HYBRID"
    CUSTOM = "CUSTOM"


class PaymentMethod(str, enum.Enum):
    BANK_CARD = "BANK_CARD"
    BANK_TRANSFER = "BANK_TRANSFER"
    USDT_TRC20 = "USDT_TRC20"
    USDT_ERC20 = "USDT_ERC20"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class BillingEventType(str, enum.Enum):
    PAYMENT_SUBMITTED = "PAYMENT_SUBMITTED"
    PAYMENT_APPROVED = "PAYMENT_APPROVED"
    PAYMENT_REJECTED = "PAYMENT_REJECTED"
    SUBSCRIPTION_ACTIVATED = "SUBSCRIPTION_ACTIVATED"
    TENANT_ACTIVATED = "TENANT_ACTIVATED"
    SUBSCRIPTION_CHANGED = "SUBSCRIPTION_CHANGED"


PRICING_MODELS = frozenset(m.value for m in PricingModel)
PAYMENT_METHODS = frozenset(m.value for m in PaymentMethod)
PAYMENT_STATUSES = frozenset(s.value for s in PaymentStatus)


class CommercialPayment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "commercial_billing_engine_v1_payments"
    __table_args__ = (
        Index("ix_commercial_billing_payments_user", "user_id"),
        Index("ix_commercial_billing_payments_tenant", "tenant_id"),
        Index("ix_commercial_billing_payments_status", "status"),
        Index("ix_commercial_billing_payments_plan", "plan_code"),
    )

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="SET NULL"),
        nullable=True,
    )
    company_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("multi_company_v1_companies.id", ondelete="SET NULL"),
        nullable=True,
    )
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenant_billing_engine_v1_subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )
    plan_code: Mapped[str] = mapped_column(String(30), nullable=False)
    pricing_model: Mapped[str] = mapped_column(String(30), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=PaymentStatus.PENDING.value,
        nullable=False,
    )
    reviewed_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<CommercialPayment user={self.user_id} plan={self.plan_code} status={self.status}>"


class PaymentReceipt(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "commercial_billing_engine_v1_payment_receipts"
    __table_args__ = (
        Index("ix_commercial_billing_receipts_payment", "payment_id"),
        Index("ix_commercial_billing_receipts_user", "uploaded_by"),
    )

    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("commercial_billing_engine_v1_payments.id", ondelete="CASCADE"),
        nullable=False,
    )
    uploaded_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    telegram_file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    telegram_file_unique_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    storage_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<PaymentReceipt payment={self.payment_id}>"


class SubscriptionHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "commercial_billing_engine_v1_subscription_history"
    __table_args__ = (
        Index("ix_commercial_billing_sub_history_tenant", "tenant_id"),
        Index("ix_commercial_billing_sub_history_subscription", "subscription_id"),
    )

    subscription_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenant_billing_engine_v1_subscriptions.id", ondelete="SET NULL"),
        nullable=True,
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    old_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    actor_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<SubscriptionHistory event={self.event_type}>"


class BillingEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "commercial_billing_engine_v1_billing_events"
    __table_args__ = (
        Index("ix_commercial_billing_events_type", "event_type"),
        Index("ix_commercial_billing_events_entity", "entity_type", "entity_id"),
        Index("ix_commercial_billing_events_tenant", "tenant_id"),
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(120), nullable=False)
    actor_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<BillingEvent {self.event_type} {self.entity_type}={self.entity_id}>"
