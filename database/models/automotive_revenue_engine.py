# Automotive Revenue Engine v1 — cross-vertical revenue, commissions, settlements.

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
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin


class RevenueServiceType(str, enum.Enum):
    INSURANCE = "INSURANCE"
    CREDIT = "CREDIT"
    LEASING = "LEASING"
    LOGISTICS = "LOGISTICS"
    NOTARY = "NOTARY"
    LEGAL = "LEGAL"
    DEALER_REFERRAL = "DEALER_REFERRAL"


class CommissionStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class SettlementStatus(str, enum.Enum):
    OPEN = "OPEN"
    PROCESSING = "PROCESSING"
    SETTLED = "SETTLED"
    FAILED = "FAILED"


class PayoutStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PAID = "PAID"
    FAILED = "FAILED"


REVENUE_SERVICE_TYPES = frozenset(s.value for s in RevenueServiceType)
COMMISSION_STATUSES = frozenset(s.value for s in CommissionStatus)


class AutomotivePartnerLead(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Partner-attributed lead (logical: partner_leads)."""

    __tablename__ = "automotive_revenue_v1_partner_leads"
    __table_args__ = (
        Index("ix_automotive_revenue_v1_partner_leads_tenant", "tenant_id"),
        Index("ix_automotive_revenue_v1_partner_leads_partner", "partner_id"),
        Index("ix_automotive_revenue_v1_partner_leads_lead", "lead_id"),
        Index("ix_automotive_revenue_v1_partner_leads_status", "commission_status"),
        Index("ix_automotive_revenue_v1_partner_leads_vertical", "vertical"),
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_partner_v1_partners.id", ondelete="CASCADE"),
        nullable=False,
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lead_automation_engine_v1_leads.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    vertical: Mapped[str] = mapped_column(String(32), nullable=False)
    commission_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0, nullable=False)
    commission_status: Mapped[str] = mapped_column(
        String(32),
        default=CommissionStatus.PENDING.value,
        nullable=False,
    )
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<AutomotivePartnerLead partner={self.partner_id} lead={self.lead_id}>"


class AutomotivePartnerCommission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Partner commission accrual (logical: partner_commissions)."""

    __tablename__ = "automotive_revenue_v1_partner_commissions"
    __table_args__ = (
        Index("ix_automotive_revenue_v1_partner_comm_tenant", "tenant_id"),
        Index("ix_automotive_revenue_v1_partner_comm_partner", "partner_id"),
        Index("ix_automotive_revenue_v1_partner_comm_status", "commission_status"),
        Index("ix_automotive_revenue_v1_partner_comm_service", "service_type"),
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_partner_v1_partners.id", ondelete="CASCADE"),
        nullable=False,
    )
    partner_lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_revenue_v1_partner_leads.id", ondelete="SET NULL"),
        nullable=True,
    )
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lead_automation_engine_v1_leads.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    service_type: Mapped[str] = mapped_column(String(32), nullable=False)
    commission_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    commission_status: Mapped[str] = mapped_column(
        String(32),
        default=CommissionStatus.PENDING.value,
        nullable=False,
    )
    rate_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    deal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<AutomotivePartnerCommission partner={self.partner_id} amount={self.commission_amount}>"


class AutomotivePartnerSettlement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Partner settlement batch (logical: partner_settlements)."""

    __tablename__ = "automotive_revenue_v1_partner_settlements"
    __table_args__ = (
        Index("ix_automotive_revenue_v1_settlements_tenant", "tenant_id"),
        Index("ix_automotive_revenue_v1_settlements_partner", "partner_id"),
        Index("ix_automotive_revenue_v1_settlements_status", "status"),
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_partner_v1_partners.id", ondelete="CASCADE"),
        nullable=False,
    )
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="UAH", nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default=SettlementStatus.OPEN.value,
        nullable=False,
    )
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<AutomotivePartnerSettlement partner={self.partner_id} total={self.total_amount}>"


class AutomotivePartnerPayout(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Partner payout record (logical: partner_payouts)."""

    __tablename__ = "automotive_revenue_v1_partner_payouts"
    __table_args__ = (
        Index("ix_automotive_revenue_v1_payouts_tenant", "tenant_id"),
        Index("ix_automotive_revenue_v1_payouts_partner", "partner_id"),
        Index("ix_automotive_revenue_v1_payouts_status", "status"),
        Index("ix_automotive_revenue_v1_payouts_settlement", "settlement_id"),
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_partner_v1_partners.id", ondelete="CASCADE"),
        nullable=False,
    )
    settlement_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_revenue_v1_partner_settlements.id", ondelete="SET NULL"),
        nullable=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="UAH", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=PayoutStatus.PENDING.value, nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<AutomotivePartnerPayout partner={self.partner_id} amount={self.amount}>"


class AutomotiveDealCommission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Deal-level commission (logical: deal_commissions)."""

    __tablename__ = "automotive_revenue_v1_deal_commissions"
    __table_args__ = (
        Index("ix_automotive_revenue_v1_deal_comm_tenant", "tenant_id"),
        Index("ix_automotive_revenue_v1_deal_comm_deal", "deal_id"),
        Index("ix_automotive_revenue_v1_deal_comm_partner", "partner_id"),
        Index("ix_automotive_revenue_v1_deal_comm_status", "commission_status"),
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
    )
    deal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    partner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_partner_v1_partners.id", ondelete="SET NULL"),
        nullable=True,
    )
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lead_automation_engine_v1_leads.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    service_type: Mapped[str] = mapped_column(String(32), nullable=False)
    commission_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    commission_status: Mapped[str] = mapped_column(
        String(32),
        default=CommissionStatus.PENDING.value,
        nullable=False,
    )
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<AutomotiveDealCommission deal={self.deal_id} amount={self.commission_amount}>"


class AutomotiveDealProfit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Deal profit snapshot (logical: deal_profit)."""

    __tablename__ = "automotive_revenue_v1_deal_profit"
    __table_args__ = (
        Index("ix_automotive_revenue_v1_deal_profit_tenant", "tenant_id"),
        Index("ix_automotive_revenue_v1_deal_profit_deal", "deal_id"),
        Index("ix_automotive_revenue_v1_deal_profit_period", "period_month"),
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
    )
    deal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lead_automation_engine_v1_leads.id", ondelete="SET NULL"),
        nullable=True,
    )
    revenue: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0, nullable=False)
    cost: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0, nullable=False)
    profit: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0, nullable=False)
    margin_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    period_month: Mapped[str | None] = mapped_column(String(7), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<AutomotiveDealProfit deal={self.deal_id} profit={self.profit}>"


class AutomotiveDealerReferral(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Dealer referral tracking (logical: dealer_referrals)."""

    __tablename__ = "automotive_revenue_v1_dealer_referrals"
    __table_args__ = (
        Index("ix_automotive_revenue_v1_referrals_tenant", "tenant_id"),
        Index("ix_automotive_revenue_v1_referrals_partner", "partner_id"),
        Index("ix_automotive_revenue_v1_referrals_lead", "lead_id"),
        Index("ix_automotive_revenue_v1_referrals_status", "commission_status"),
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
    )
    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_partner_v1_partners.id", ondelete="CASCADE"),
        nullable=False,
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lead_automation_engine_v1_leads.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    referrer_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="NEW", nullable=False)
    commission_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0, nullable=False)
    commission_status: Mapped[str] = mapped_column(
        String(32),
        default=CommissionStatus.PENDING.value,
        nullable=False,
    )
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<AutomotiveDealerReferral partner={self.partner_id} lead={self.lead_id}>"
