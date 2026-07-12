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


class CostItemType(str, enum.Enum):
    PURCHASE = "PURCHASE"
    AUCTION_FEE = "AUCTION_FEE"
    LOGISTICS = "LOGISTICS"
    CUSTOMS = "CUSTOMS"
    REPAIR = "REPAIR"
    MARGIN = "MARGIN"
    OTHER = "OTHER"


class MarginRuleType(str, enum.Enum):
    PERCENT = "PERCENT"
    FIXED = "FIXED"
    TIERED = "TIERED"


class LogisticsRoute(str, enum.Enum):
    USA_ODESSA = "USA_ODESSA"
    USA_KYIV = "USA_KYIV"
    EU_ODESSA = "EU_ODESSA"
    LOCAL = "LOCAL"


class VehicleCost(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_cost_v1_vehicle_costs"
    __table_args__ = (
        UniqueConstraint("vehicle_id", name="uq_automotive_cost_v1_vehicle_costs_vehicle_id"),
        CheckConstraint("total_amount >= 0", name="ck_automotive_cost_v1_vc_total"),
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
    purchase_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    subtotal_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0"),
        nullable=False,
    )
    margin_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0"),
        nullable=False,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0"),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<VehicleCost id={self.id} vehicle={self.vehicle_id} "
            f"total={self.total_amount}>"
        )


class CostItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_cost_v1_cost_items"
    __table_args__ = (
        Index("ix_automotive_cost_v1_ci_vehicle_cost_id", "vehicle_cost_id"),
        Index("ix_automotive_cost_v1_ci_item_type", "item_type"),
    )

    vehicle_cost_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_cost_v1_vehicle_costs.id", ondelete="CASCADE"),
        nullable=False,
    )
    item_type: Mapped[str] = mapped_column(String(30), nullable=False)
    label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    is_calculated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    calculation_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<CostItem id={self.id} type={self.item_type} amount={self.amount}>"
        )


class MarginRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_cost_v1_margin_rules"
    __table_args__ = (
        Index("ix_automotive_cost_v1_mr_is_active", "is_active"),
        Index("ix_automotive_cost_v1_mr_priority", "priority"),
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
        return f"<MarginRule id={self.id} name={self.name} type={self.rule_type}>"
