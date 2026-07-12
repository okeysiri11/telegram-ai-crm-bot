# Universal deal models + module extensions.

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from database.models.commissions import Commission
    from database.models.ledger import LedgerEntry
    from database.models.partners import PartnerDealAssignment
    from database.models.users import User


class Deal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "deals"
    __table_args__ = (
        Index("ix_deals_module", "module"),
        Index("ix_deals_status", "status"),
        Index("ix_deals_public_id", "public_id", unique=True),
        Index("ix_deals_owner_id", "owner_id"),
        Index("ix_deals_manager_id", "manager_id"),
        Index("ix_deals_legacy_ref", "legacy_ref_type", "legacy_ref_id"),
    )

    module: Mapped[str] = mapped_column(String(32), nullable=False)
    deal_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="NEW", nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False,
    )
    manager_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    partner_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="USD", nullable=False)
    profit: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    commission: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    public_id: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    legacy_ref_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    legacy_ref_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    owner: Mapped[User] = relationship(foreign_keys=[owner_id])
    manager: Mapped[User | None] = relationship(foreign_keys=[manager_id])
    commissions: Mapped[list[Commission]] = relationship(
        back_populates="deal", cascade="all, delete-orphan",
    )
    ledger_entries: Mapped[list[LedgerEntry]] = relationship(
        back_populates="deal", cascade="all, delete-orphan",
    )
    partner_assignments: Mapped[list[PartnerDealAssignment]] = relationship(
        back_populates="deal", cascade="all, delete-orphan",
    )
    agro_ext: Mapped[DealAgroExt | None] = relationship(
        back_populates="deal", cascade="all, delete-orphan", uselist=False,
    )
    auto_ext: Mapped[DealAutoExt | None] = relationship(
        back_populates="deal", cascade="all, delete-orphan", uselist=False,
    )
    legal_ext: Mapped[DealLegalExt | None] = relationship(
        back_populates="deal", cascade="all, delete-orphan", uselist=False,
    )
    drone_ext: Mapped[DealDroneExt | None] = relationship(
        back_populates="deal", cascade="all, delete-orphan", uselist=False,
    )
    finance_ext: Mapped[DealFinanceExt | None] = relationship(
        back_populates="deal", cascade="all, delete-orphan", uselist=False,
    )
    logistics_ext: Mapped[DealLogisticsExt | None] = relationship(
        back_populates="deal", cascade="all, delete-orphan", uselist=False,
    )


class DealAgroExt(Base):
    __tablename__ = "deal_agro_ext"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), primary_key=True,
    )
    request_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    product: Mapped[str | None] = mapped_column(String(255), nullable=True)
    erp_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    legacy_agro_deal_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    deal: Mapped[Deal] = relationship(back_populates="agro_ext")


class DealAutoExt(Base):
    __tablename__ = "deal_auto_ext"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), primary_key=True,
    )
    vehicle_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vin: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tradein_flag: Mapped[bool] = mapped_column(default=False, nullable=False)

    deal: Mapped[Deal] = relationship(back_populates="auto_ext")


class DealLegalExt(Base):
    __tablename__ = "deal_legal_ext"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), primary_key=True,
    )
    case_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    court_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    case_type: Mapped[str | None] = mapped_column(String(128), nullable=True)

    deal: Mapped[Deal] = relationship(back_populates="legal_ext")


class DealDroneExt(Base):
    __tablename__ = "deal_drone_ext"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), primary_key=True,
    )
    project_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    drone_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    delivery_date: Mapped[str | None] = mapped_column(String(32), nullable=True)

    deal: Mapped[Deal] = relationship(back_populates="drone_ext")


class DealFinanceExt(Base):
    __tablename__ = "deal_finance_ext"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), primary_key=True,
    )
    finance_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("finance_transactions.id", ondelete="SET NULL"),
        nullable=True,
    )
    finance_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("finance_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    payment_terms: Mapped[str | None] = mapped_column(String(255), nullable=True)

    deal: Mapped[Deal] = relationship(back_populates="finance_ext")


class DealLogisticsExt(Base):
    __tablename__ = "deal_logistics_ext"

    deal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("deals.id", ondelete="CASCADE"), primary_key=True,
    )
    route: Mapped[str | None] = mapped_column(String(512), nullable=True)
    shipment_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    origin: Mapped[str | None] = mapped_column(String(255), nullable=True)
    destination: Mapped[str | None] = mapped_column(String(255), nullable=True)

    deal: Mapped[Deal] = relationship(back_populates="logistics_ext")
