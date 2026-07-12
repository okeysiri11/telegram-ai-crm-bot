# Treasury Engine models — accounts, transfers, liquidity reservations.

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

import database.models.deal  # noqa: F401 — register deal_engine_deals for FK resolution


class TreasuryAccountType(str, enum.Enum):
    OPERATING = "OPERATING"
    SETTLEMENT = "SETTLEMENT"
    RESERVE = "RESERVE"
    ESCROW = "ESCROW"


class TreasuryAccountStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    CLOSED = "CLOSED"


class TreasuryTransferStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVERSED = "REVERSED"


class TreasuryTransferType(str, enum.Enum):
    INTERNAL = "INTERNAL"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"


class LiquidityReservationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    CONSUMED = "CONSUMED"


class TreasuryAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "treasury_engine_accounts"
    __table_args__ = (
        CheckConstraint("balance >= 0", name="ck_treasury_engine_accounts_balance"),
        CheckConstraint(
            "reserved_balance >= 0",
            name="ck_treasury_engine_accounts_reserved_balance",
        ),
        CheckConstraint(
            "reserved_balance <= balance",
            name="ck_treasury_engine_accounts_reserved_lte_balance",
        ),
        UniqueConstraint("code", "asset", name="uq_treasury_engine_accounts_code_asset"),
        Index("ix_treasury_engine_accounts_asset", "asset"),
        Index("ix_treasury_engine_accounts_status", "status"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    asset: Mapped[str] = mapped_column(String(20), nullable=False)
    account_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=TreasuryAccountStatus.ACTIVE.value,
        nullable=False,
    )
    balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        default=Decimal("0"),
        nullable=False,
    )
    reserved_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 8),
        default=Decimal("0"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<TreasuryAccount id={self.id} code={self.code} "
            f"balance={self.balance} reserved={self.reserved_balance} {self.asset}>"
        )

    @property
    def available_balance(self) -> Decimal:
        return self.balance - self.reserved_balance


class TreasuryTransfer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "treasury_engine_transfers"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_treasury_engine_transfers_amount"),
        Index("ix_treasury_engine_transfers_from_account_id", "from_account_id"),
        Index("ix_treasury_engine_transfers_to_account_id", "to_account_id"),
        Index("ix_treasury_engine_transfers_status", "status"),
        Index("ix_treasury_engine_transfers_deal_id", "deal_id"),
    )

    from_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("treasury_engine_accounts.id", ondelete="RESTRICT"),
        nullable=False,
    )
    to_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("treasury_engine_accounts.id", ondelete="RESTRICT"),
        nullable=False,
    )
    deal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deal_engine_deals.id", ondelete="SET NULL"),
        nullable=True,
    )
    asset: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    transfer_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=TreasuryTransferStatus.PENDING.value,
        nullable=False,
    )
    reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<TreasuryTransfer id={self.id} {self.amount} {self.asset} "
            f"{self.from_account_id} -> {self.to_account_id} status={self.status}>"
        )


class LiquidityReservation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "treasury_engine_liquidity_reservations"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_treasury_engine_reservations_amount"),
        Index("ix_treasury_engine_reservations_account_id", "account_id"),
        Index("ix_treasury_engine_reservations_deal_id", "deal_id"),
        Index("ix_treasury_engine_reservations_status", "status"),
    )

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("treasury_engine_accounts.id", ondelete="RESTRICT"),
        nullable=False,
    )
    deal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deal_engine_deals.id", ondelete="SET NULL"),
        nullable=True,
    )
    asset: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=LiquidityReservationStatus.ACTIVE.value,
        nullable=False,
    )
    reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<LiquidityReservation id={self.id} account={self.account_id} "
            f"amount={self.amount} {self.asset} status={self.status}>"
        )
