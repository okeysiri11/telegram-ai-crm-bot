# Partner Cabinet v1 — partner profiles, commissions, payouts.

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin


class PartnerCabinetRole(str, enum.Enum):
    INSURANCE = "insurance"
    LEASING = "leasing"
    BANKS = "banks"
    LOGISTICS = "logistics"
    LEGAL = "legal"
    DEALERS = "dealers"
    SERVICE_STATIONS = "service_stations"


PARTNER_CABINET_ROLE_DISPLAY = {
    PartnerCabinetRole.INSURANCE.value: "Insurance",
    PartnerCabinetRole.LEASING.value: "Leasing",
    PartnerCabinetRole.BANKS.value: "Banks",
    PartnerCabinetRole.LOGISTICS.value: "Logistics",
    PartnerCabinetRole.LEGAL.value: "Legal",
    PartnerCabinetRole.DEALERS.value: "Dealers",
    PartnerCabinetRole.SERVICE_STATIONS.value: "Service stations",
}

PARTNER_TYPE_TO_CABINET_ROLE = {
    "INSURANCE": PartnerCabinetRole.INSURANCE.value,
    "LEASING": PartnerCabinetRole.LEASING.value,
    "CREDIT": PartnerCabinetRole.BANKS.value,
    "LOGISTICS": PartnerCabinetRole.LOGISTICS.value,
    "LEGAL": PartnerCabinetRole.LEGAL.value,
    "DEALER": PartnerCabinetRole.DEALERS.value,
    "DELIVERY": PartnerCabinetRole.LOGISTICS.value,
    "SERVICE_STATION": PartnerCabinetRole.SERVICE_STATIONS.value,
}


class PartnerCabinetCommissionStatus(str, enum.Enum):
    ACCRUED = "ACCRUED"
    PENDING = "PENDING"
    PAID = "PAID"


class PartnerCabinetV1Profile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "partner_cabinet_v1_profiles"
    __table_args__ = (
        UniqueConstraint("partner_id", name="uq_partner_cabinet_v1_partner"),
        UniqueConstraint("telegram_user_id", name="uq_partner_cabinet_v1_telegram"),
        Index("ix_partner_cabinet_v1_role", "cabinet_role"),
        Index("ix_partner_cabinet_v1_blocked", "is_blocked"),
    )

    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_partner_v1_partners.id", ondelete="CASCADE"),
        nullable=False,
    )
    telegram_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    cabinet_role: Mapped[str] = mapped_column(String(50), nullable=False)
    commission_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    blocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    blocked_by_telegram_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)


class PartnerCabinetV1Commission(CreatedAtMixin, UUIDPrimaryKeyMixin, Base):
    __tablename__ = "partner_cabinet_v1_commissions"
    __table_args__ = (
        UniqueConstraint("revenue_entry_id", name="uq_partner_cabinet_v1_revenue"),
        Index("ix_partner_cabinet_v1_comm_partner", "partner_id"),
        Index("ix_partner_cabinet_v1_comm_status", "status"),
        Index("ix_partner_cabinet_v1_comm_deal", "deal_id"),
    )

    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_partner_v1_partners.id", ondelete="CASCADE"),
        nullable=False,
    )
    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deal_engine_v1_deals.id", ondelete="CASCADE"),
        nullable=False,
    )
    revenue_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("revenue_engine_v1_entries.id", ondelete="CASCADE"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=PartnerCabinetCommissionStatus.ACCRUED.value,
        nullable=False,
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by_telegram_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_by_telegram_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
