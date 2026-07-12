# Ledger Engine model — double-entry ledger foundation.

from __future__ import annotations

import enum
import uuid
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin

import database.models.deal  # noqa: F401 — register deal_engine_deals for FK resolution


class LedgerDirection(str, enum.Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class LedgerAccountType(str, enum.Enum):
    CASH_DESK = "CASH_DESK"
    BANK_ACCOUNT = "BANK_ACCOUNT"
    CRYPTO_WALLET = "CRYPTO_WALLET"
    CLIENT = "CLIENT"
    PARTNER = "PARTNER"
    MANAGER = "MANAGER"
    COMPANY = "COMPANY"


class LedgerEntry(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "ledger_engine_entries"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_ledger_engine_entries_amount_positive"),
        CheckConstraint(
            "direction IN ('DEBIT', 'CREDIT')",
            name="ck_ledger_engine_entries_direction",
        ),
        Index("ix_ledger_engine_entries_deal_id", "deal_id"),
        Index("ix_ledger_engine_entries_account_type", "account_type"),
        Index("ix_ledger_engine_entries_account_id", "account_id"),
        Index("ix_ledger_engine_entries_asset", "asset"),
    )

    deal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deal_engine_deals.id", ondelete="SET NULL"),
        nullable=True,
    )
    account_type: Mapped[str] = mapped_column(String(50), nullable=False)
    account_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    asset: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)

    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<LedgerEntry id={self.id} {self.direction} "
            f"{self.amount} {self.asset} account={self.account_type}:{self.account_id}>"
        )
