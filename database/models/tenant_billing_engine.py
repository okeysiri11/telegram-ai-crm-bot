# Tenant Billing Engine v1 — subscriptions, usage metering, invoices.

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class BillingPlanCode(str, enum.Enum):
    STARTER = "STARTER"
    PRO = "PRO"
    BUSINESS = "BUSINESS"
    ENTERPRISE = "ENTERPRISE"


BILLING_PLAN_CODES = frozenset(p.value for p in BillingPlanCode)


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"
    PAST_DUE = "PAST_DUE"


class UsageBillingType(str, enum.Enum):
    MONTHLY_SUBSCRIPTION = "monthly_subscription"
    USAGE = "usage"
    PER_LEAD = "per_lead"
    PER_MANAGER = "per_manager"
    PER_CHANNEL = "per_channel"


USAGE_BILLING_TYPES = frozenset(t.value for t in UsageBillingType)


class InvoiceStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    PAID = "PAID"
    VOID = "VOID"


class TenantSubscription(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenant_billing_engine_v1_subscriptions"
    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_tenant_billing_engine_v1_subscriptions_tenant"),
        Index("ix_tenant_billing_engine_v1_subscriptions_company", "company_id"),
        Index("ix_tenant_billing_engine_v1_subscriptions_plan", "plan_code"),
        Index("ix_tenant_billing_engine_v1_subscriptions_status", "status"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("multi_company_v1_companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    plan_code: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=SubscriptionStatus.ACTIVE.value,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    current_period_start: Mapped[date] = mapped_column(Date, nullable=False)
    current_period_end: Mapped[date] = mapped_column(Date, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<TenantSubscription tenant={self.tenant_id} plan={self.plan_code}>"


class TenantUsageRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenant_billing_engine_v1_usage_records"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_tenant_billing_engine_v1_usage_qty"),
        CheckConstraint("amount >= 0", name="ck_tenant_billing_engine_v1_usage_amount"),
        UniqueConstraint(
            "tenant_id",
            "billing_type",
            "reference_key",
            name="uq_tenant_billing_engine_v1_usage_tenant_type_ref",
        ),
        Index("ix_tenant_billing_engine_v1_usage_tenant", "tenant_id"),
        Index("ix_tenant_billing_engine_v1_usage_company", "company_id"),
        Index("ix_tenant_billing_engine_v1_usage_type", "billing_type"),
        Index("ix_tenant_billing_engine_v1_usage_recorded", "recorded_at"),
        Index("ix_tenant_billing_engine_v1_usage_invoice", "invoice_id"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("multi_company_v1_companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    billing_type: Mapped[str] = mapped_column(String(40), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    reference_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenant_billing_engine_v1_invoices.id", ondelete="SET NULL"),
        nullable=True,
    )
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<TenantUsageRecord tenant={self.tenant_id} type={self.billing_type}>"


class TenantInvoice(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenant_billing_engine_v1_invoices"
    __table_args__ = (
        UniqueConstraint("invoice_number", name="uq_tenant_billing_engine_v1_invoices_number"),
        CheckConstraint("subtotal >= 0", name="ck_tenant_billing_engine_v1_invoices_subtotal"),
        CheckConstraint("total >= 0", name="ck_tenant_billing_engine_v1_invoices_total"),
        Index("ix_tenant_billing_engine_v1_invoices_tenant", "tenant_id"),
        Index("ix_tenant_billing_engine_v1_invoices_company", "company_id"),
        Index("ix_tenant_billing_engine_v1_invoices_status", "status"),
        Index("ix_tenant_billing_engine_v1_invoices_period", "period_start", "period_end"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("multi_company_v1_companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    invoice_number: Mapped[str] = mapped_column(String(64), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=InvoiceStatus.ISSUED.value,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    tax: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    generated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<TenantInvoice number={self.invoice_number} total={self.total}>"


class TenantInvoiceLine(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenant_billing_engine_v1_invoice_lines"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_tenant_billing_engine_v1_lines_amount"),
        Index("ix_tenant_billing_engine_v1_lines_invoice", "invoice_id"),
        Index("ix_tenant_billing_engine_v1_lines_type", "line_type"),
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenant_billing_engine_v1_invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    line_type: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<TenantInvoiceLine invoice={self.invoice_id} type={self.line_type}>"
