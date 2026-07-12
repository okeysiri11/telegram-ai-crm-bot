# Finance models (referenced by ledger & commissions).

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from database.models.ledger import LedgerEntry
    from database.models.commissions import Commission, CommissionPayment
    from database.models.users import User


class FinanceAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "finance_accounts"
    __table_args__ = (
        Index("ix_finance_accounts_type", "account_type"),
        Index("ix_finance_accounts_status", "status"),
    )

    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_type: Mapped[str] = mapped_column(String(64), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)


class FinanceTransaction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "finance_transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_finance_transactions_amount_positive"),
        Index("ix_finance_transactions_status", "status"),
        Index("ix_finance_transactions_reference", "reference_type", "reference_id"),
    )

    transaction_type: Mapped[str] = mapped_column(String(64), nullable=False)
    debit_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("finance_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    credit_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("finance_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="CREATED", nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by: Mapped[User] = relationship(foreign_keys=[created_by_id])
    ledger_entries: Mapped[list[LedgerEntry]] = relationship(back_populates="finance_transaction")
    commissions: Mapped[list[Commission]] = relationship(back_populates="finance_transaction")
    commission_payments: Mapped[list[CommissionPayment]] = relationship(
        back_populates="finance_transaction",
    )
