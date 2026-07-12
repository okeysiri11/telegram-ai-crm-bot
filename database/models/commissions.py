# Commission engine models.

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from database.models.deals import Deal
    from database.models.finance import FinanceTransaction
    from database.models.users import User


class CommissionRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "commission_rules"
    __table_args__ = (
        Index("ix_commission_rules_type", "commission_type"),
        Index("ix_commission_rules_active", "active"),
    )

    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    commission_type: Mapped[str] = mapped_column(String(32), nullable=False)
    module: Mapped[str | None] = mapped_column(String(32), nullable=True)
    rate_type: Mapped[str] = mapped_column(String(16), default="PERCENT", nullable=False)
    rate_value: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    min_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    max_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    commissions: Mapped[list[Commission]] = relationship(back_populates="rule")


class Commission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "commissions"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_commissions_amount_non_negative"),
        Index("ix_commissions_recipient", "recipient_id"),
        Index("ix_commissions_deal_id", "deal_id"),
        Index("ix_commissions_status", "status"),
        Index("ix_commissions_type", "commission_type"),
    )

    recipient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False,
    )
    recipient_role: Mapped[str] = mapped_column(String(64), nullable=False)
    commission_type: Mapped[str] = mapped_column(String(32), nullable=False)
    deal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="SET NULL"), nullable=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("commission_rules.id", ondelete="SET NULL"), nullable=True,
    )
    payment_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    finance_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("finance_transactions.id", ondelete="SET NULL"),
        nullable=True,
    )
    module: Mapped[str | None] = mapped_column(String(32), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    recipient: Mapped[User] = relationship(foreign_keys=[recipient_id])
    deal: Mapped[Deal | None] = relationship(back_populates="commissions")
    rule: Mapped[CommissionRule | None] = relationship(back_populates="commissions")
    finance_transaction: Mapped[FinanceTransaction | None] = relationship(
        back_populates="commissions",
    )
    payments: Mapped[list[CommissionPayment]] = relationship(
        back_populates="commission",
        cascade="all, delete-orphan",
    )


class CommissionPayment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "commission_payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_commission_payments_amount_positive"),
        Index("ix_commission_payments_commission_id", "commission_id"),
    )

    commission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("commissions.id", ondelete="CASCADE"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    payment_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    finance_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("finance_transactions.id", ondelete="SET NULL"),
        nullable=True,
    )
    paid_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    commission: Mapped[Commission] = relationship(back_populates="payments")
    finance_transaction: Mapped[FinanceTransaction | None] = relationship(
        back_populates="commission_payments",
    )
    paid_by: Mapped[User | None] = relationship(foreign_keys=[paid_by_id])
