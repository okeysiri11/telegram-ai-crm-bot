# Partner Hub models.

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from database.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from database.models.deals import Deal
    from database.models.users import User


class Partner(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "partners"
    __table_args__ = (
        Index("ix_partners_type", "partner_type"),
        Index("ix_partners_company", "company_name"),
        Index("ix_partners_public_id", "public_id", unique=True),
        Index("ix_partners_active", "active"),
        Index("ix_partners_telegram_id", "telegram_id"),
    )

    partner_type: Mapped[str] = mapped_column(String(32), nullable=False)
    company_name: Mapped[str] = mapped_column(String(512), nullable=False)
    contact_person: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_id: Mapped[int | None] = mapped_column(nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rating: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    regions: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    services: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    public_id: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )

    created_by: Mapped[User | None] = relationship(foreign_keys=[created_by_id])
    deal_assignments: Mapped[list[PartnerDealAssignment]] = relationship(
        back_populates="partner", cascade="all, delete-orphan",
    )
    kpi_records: Mapped[list[PartnerKpi]] = relationship(
        back_populates="partner", cascade="all, delete-orphan",
    )


class PartnerDealAssignment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "partner_deal_assignments"
    __table_args__ = (
        UniqueConstraint("partner_id", "deal_id", name="uq_partner_deal_assignments"),
        Index("ix_partner_deal_assignments_deal_id", "deal_id"),
    )

    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False,
    )
    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False,
    )
    assignment_role: Mapped[str] = mapped_column(String(64), default="PARTNER", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)
    assigned_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    partner: Mapped[Partner] = relationship(back_populates="deal_assignments")
    deal: Mapped[Deal] = relationship(back_populates="partner_assignments")
    assigned_by: Mapped[User] = relationship(foreign_keys=[assigned_by_id])


class PartnerKpi(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "partner_kpi"
    __table_args__ = (
        UniqueConstraint("partner_id", "period", name="uq_partner_kpi_period"),
        Index("ix_partner_kpi_partner_id", "partner_id"),
    )

    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False,
    )
    period: Mapped[str] = mapped_column(String(16), nullable=False)
    deals_count: Mapped[int] = mapped_column(default=0, nullable=False)
    deals_completed: Mapped[int] = mapped_column(default=0, nullable=False)
    total_volume: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    total_commission: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, nullable=False)
    avg_rating: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)

    partner: Mapped[Partner] = relationship(back_populates="kpi_records")
