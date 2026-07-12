# Internal ledger models.

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
    from database.models.deals import Deal
    from database.models.finance import FinanceTransaction
    from database.models.users import User


class LedgerEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ledger_entries"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_ledger_entries_amount_positive"),
        Index("ix_ledger_entries_entry_id", "entry_id", unique=True),
        Index("ix_ledger_entries_deal_id", "deal_id"),
        Index("ix_ledger_entries_module", "module"),
        Index("ix_ledger_entries_entry_type", "entry_type"),
        Index("ix_ledger_entries_status", "status"),
    )

    entry_id: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    deal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deals.id", ondelete="SET NULL"),
        nullable=True,
    )
    module: Mapped[str] = mapped_column(String(32), nullable=False)
    entry_type: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="POSTED", nullable=False)
    finance_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("finance_transactions.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    deal: Mapped[Deal | None] = relationship(back_populates="ledger_entries")
    finance_transaction: Mapped[FinanceTransaction | None] = relationship(
        back_populates="ledger_entries",
    )
    created_by: Mapped[User] = relationship(foreign_keys=[created_by_id])
