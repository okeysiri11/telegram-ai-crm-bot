# Automotive Cost Engine v1 — vehicle costs, cost items, margin rules.

from __future__ import annotations

import enum
import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin

import database.models.automotive_inventory  # noqa: F401


class VehicleCostStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    CALCULATED = "CALCULATED"
    APPROVED = "APPROVED"
    LOCKED = "LOCKED"


class CostType(str, enum.Enum):
    PURCHASE = "PURCHASE"
    AUCTION_FEE = "AUCTION_FEE"
    TRANSPORT = "TRANSPORT"
    PORT = "PORT"
    CUSTOMS = "CUSTOMS"
    CERTIFICATION = "CERTIFICATION"
    REPAIR = "REPAIR"
    DETAILING = "DETAILING"
    ADVERTISING = "ADVERTISING"
    COMMISSION = "COMMISSION"
    INSURANCE = "INSURANCE"
    OTHER = "OTHER"


class MarginRuleType(str, enum.Enum):
    PERCENT = "PERCENT"
    FIXED = "FIXED"
    TIERED = "TIERED"


class VehicleCost(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_cost_v1_vehicle_costs"
    __table_args__ = (
        UniqueConstraint("vehicle_id", name="uq_automotive_cost_v1_vehicle_costs_vehicle_id"),
        CheckConstraint("total_cost >= 0", name="ck_automotive_cost_v1_vc_total_cost"),
        Index("ix_automotive_cost_v1_vc_status", "status"),
    )

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_v1_vehicles.id", ondelete="CASCADE"),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=VehicleCostStatus.DRAFT.value,
        nullable=False,
    )
    total_cost: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0"),
        nullable=False,
    )
    margin_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0"),
        nullable=False,
    )
    target_price: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0"),
        nullable=False,
    )
    roi_percent: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<VehicleCost id={self.id} vehicle={self.vehicle_id} "
            f"target={self.target_price}>"
        )


class VehicleCostItem(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "automotive_cost_v1_vehicle_cost_items"
    __table_args__ = (
        Index("ix_automotive_cost_v1_vci_vehicle_id", "vehicle_id"),
        Index("ix_automotive_cost_v1_vci_cost_type", "cost_type"),
    )

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_v1_vehicles.id", ondelete="CASCADE"),
        nullable=False,
    )
    cost_type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)

    def __repr__(self) -> str:
        return (
            f"<VehicleCostItem id={self.id} vehicle={self.vehicle_id} "
            f"type={self.cost_type} amount={self.amount}>"
        )


class VehicleMarginRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_cost_v1_vehicle_margin_rules"
    __table_args__ = (
        Index("ix_automotive_cost_v1_vmr_is_active", "is_active"),
        Index("ix_automotive_cost_v1_vmr_priority", "priority"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(20), nullable=False)
    min_base_amount: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    max_base_amount: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    margin_percent: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    margin_fixed: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<VehicleMarginRule id={self.id} name={self.name} type={self.rule_type}>"
