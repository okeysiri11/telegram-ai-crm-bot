# Commission Engine model — deal commission foundation.

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin

import database.models.deal  # noqa: F401 — register deal_engine_deals for FK resolution


class CommissionType(str, enum.Enum):
    CLIENT_FEE = "CLIENT_FEE"
    MANAGER_REWARD = "MANAGER_REWARD"
    PARTNER_REWARD = "PARTNER_REWARD"
    COMPANY_PROFIT = "COMPANY_PROFIT"


class CommissionStatus(str, enum.Enum):
    PENDING = "PENDING"
    CALCULATED = "CALCULATED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class Commission(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "commission_engine_commissions"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_commission_engine_amount_non_negative"),
        Index("ix_commission_engine_deal_id", "deal_id"),
        Index("ix_commission_engine_manager_id", "manager_id"),
        Index("ix_commission_engine_partner_id", "partner_id"),
        Index("ix_commission_engine_status", "status"),
    )

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deal_engine_deals.id", ondelete="CASCADE"),
        nullable=False,
    )
    manager_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    partner_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    commission_type: Mapped[str] = mapped_column(String(30), nullable=False)
    asset: Mapped[str] = mapped_column(String(20), nullable=False)

    percentage: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)

    status: Mapped[str] = mapped_column(
        String(20),
        default=CommissionStatus.PENDING.value,
        nullable=False,
    )
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<Commission id={self.id} type={self.commission_type} "
            f"amount={self.amount} {self.asset} status={self.status}>"
        )
