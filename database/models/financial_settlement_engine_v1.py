# Financial Settlement Engine v1 — revenues, commissions, settlements, treasury.

from __future__ import annotations

import enum
import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin


class FinancialSettlementStatus(str, enum.Enum):
    PENDING = "PENDING"
    SETTLED = "SETTLED"
    FAILED = "FAILED"


class FinancialCommissionRecipientType(str, enum.Enum):
    PARTNER = "PARTNER"
    MANAGER = "MANAGER"
    REFERRAL = "REFERRAL"


class FinancialCommissionStatus(str, enum.Enum):
    ACCRUED = "ACCRUED"
    PENDING_PAYOUT = "PENDING_PAYOUT"
    PAID = "PAID"


class FinancialTreasuryTransactionType(str, enum.Enum):
    CLIENT_PAYMENT = "client_payment"
    PARTNER_SHARE = "partner_share"
    MANAGER_SHARE = "manager_share"
    PLATFORM_PROFIT = "platform_profit"
    REFERRAL_SHARE = "referral_share"


class FinancialTreasuryDirection(str, enum.Enum):
    IN = "IN"
    OUT = "OUT"


FINANCIAL_SETTLEMENT_STATUSES = frozenset(s.value for s in FinancialSettlementStatus)
FINANCIAL_COMMISSION_STATUSES = frozenset(s.value for s in FinancialCommissionStatus)


class FinancialSettlementV1Revenue(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """Revenue record created when a payment is confirmed."""

    __tablename__ = "financial_settlement_v1_revenues"
    __table_args__ = (
        UniqueConstraint("payment_id", name="uq_fin_settlement_v1_revenue_payment"),
        Index("ix_fin_settlement_v1_revenue_deal", "deal_id"),
        Index("ix_fin_settlement_v1_revenue_created", "created_at"),
    )

    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payment_engine_v1_payments.id", ondelete="CASCADE"),
        nullable=False,
    )
    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deal_engine_v1_deals.id", ondelete="CASCADE"),
        nullable=False,
    )
    revenue_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("revenue_engine_v1_entries.id", ondelete="SET NULL"),
        nullable=True,
    )
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    platform_profit: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)


class FinancialSettlementV1Settlement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "financial_settlement_v1_settlements"
    __table_args__ = (
        UniqueConstraint("payment_id", name="uq_fin_settlement_v1_settlement_payment"),
        Index("ix_fin_settlement_v1_settlement_deal", "deal_id"),
        Index("ix_fin_settlement_v1_settlement_status", "status"),
        Index("ix_fin_settlement_v1_settlement_created", "created_at"),
    )

    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payment_engine_v1_payments.id", ondelete="CASCADE"),
        nullable=False,
    )
    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deal_engine_v1_deals.id", ondelete="CASCADE"),
        nullable=False,
    )
    revenue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("financial_settlement_v1_revenues.id", ondelete="CASCADE"),
        nullable=False,
    )
    partner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_partner_v1_partners.id", ondelete="SET NULL"),
        nullable=True,
    )
    manager_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    client_payment: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    partner_share: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"), nullable=False)
    manager_share: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"), nullable=False)
    platform_profit: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    referral_share: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        default=FinancialSettlementStatus.PENDING.value,
        nullable=False,
    )


class FinancialSettlementV1Commission(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "financial_settlement_v1_commissions"
    __table_args__ = (
        Index("ix_fin_settlement_v1_comm_settlement", "settlement_id"),
        Index("ix_fin_settlement_v1_comm_recipient", "recipient_type", "recipient_id"),
        Index("ix_fin_settlement_v1_comm_status", "status"),
    )

    settlement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("financial_settlement_v1_settlements.id", ondelete="CASCADE"),
        nullable=False,
    )
    recipient_type: Mapped[str] = mapped_column(String(50), nullable=False)
    recipient_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        default=FinancialCommissionStatus.ACCRUED.value,
        nullable=False,
    )


class FinancialSettlementV1TreasuryTransaction(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "financial_settlement_v1_treasury_transactions"
    __table_args__ = (
        Index("ix_fin_settlement_v1_treasury_payment", "payment_id"),
        Index("ix_fin_settlement_v1_treasury_settlement", "settlement_id"),
        Index("ix_fin_settlement_v1_treasury_type", "transaction_type"),
        Index("ix_fin_settlement_v1_treasury_created", "created_at"),
    )

    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payment_engine_v1_payments.id", ondelete="CASCADE"),
        nullable=False,
    )
    settlement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("financial_settlement_v1_settlements.id", ondelete="CASCADE"),
        nullable=False,
    )
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
