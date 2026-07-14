# Universal Revenue Engine v1 — revenue entries from completed deals.

from __future__ import annotations

import enum
import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class RevenueEngineV1PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"


REVENUE_ENGINE_V1_PAYMENT_STATUSES = frozenset(s.value for s in RevenueEngineV1PaymentStatus)
REVENUE_ENGINE_V1_SUPPORTED_VERTICALS = frozenset({"auto", "agro"})


class RevenueEngineV1Entry(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "revenue_engine_v1_entries"
    __table_args__ = (
        UniqueConstraint("deal_id", name="uq_revenue_engine_v1_deal"),
        Index("ix_revenue_engine_v1_deal", "deal_id"),
        Index("ix_revenue_engine_v1_payment_status", "payment_status"),
        Index("ix_revenue_engine_v1_created", "created_at"),
        Index("ix_revenue_engine_v1_currency", "currency"),
    )

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deal_engine_v1_deals.id", ondelete="CASCADE"),
        nullable=False,
    )

    gross_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    platform_income: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    partner_income: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"), nullable=False)
    manager_income: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"), nullable=False)
    referral_income: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"), nullable=False)

    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    payment_status: Mapped[str] = mapped_column(
        String(50),
        default=RevenueEngineV1PaymentStatus.PENDING.value,
        nullable=False,
    )
