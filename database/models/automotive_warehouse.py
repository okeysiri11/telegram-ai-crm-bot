# Automotive Parts Warehouse Engine v1 — parts, suppliers, stock, reservations.

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
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

import database.models.automotive_service  # noqa: F401


class StockMovementType(str, enum.Enum):
    IN = "IN"
    OUT = "OUT"
    ADJUSTMENT = "ADJUSTMENT"
    RESERVE = "RESERVE"
    RELEASE = "RELEASE"
    CONSUME = "CONSUME"


class StockReferenceType(str, enum.Enum):
    SERVICE_ORDER = "SERVICE_ORDER"
    PURCHASE = "PURCHASE"
    MANUAL = "MANUAL"
    REORDER = "REORDER"


class PartReservationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class Supplier(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_warehouse_v1_suppliers"
    __table_args__ = (
        Index("ix_automotive_warehouse_v1_suppliers_is_active", "is_active"),
        Index("ix_automotive_warehouse_v1_suppliers_name", "name"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Supplier id={self.id} name={self.name}>"


class Part(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_warehouse_v1_parts"
    __table_args__ = (
        UniqueConstraint("part_number", name="uq_automotive_warehouse_v1_parts_part_number"),
        CheckConstraint("quantity_on_hand >= 0", name="ck_automotive_warehouse_v1_parts_on_hand"),
        CheckConstraint("quantity_reserved >= 0", name="ck_automotive_warehouse_v1_parts_reserved"),
        CheckConstraint("min_stock_level >= 0", name="ck_automotive_warehouse_v1_parts_min"),
        Index("ix_automotive_warehouse_v1_parts_supplier_id", "supplier_id"),
        Index("ix_automotive_warehouse_v1_parts_is_active", "is_active"),
    )

    part_number: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_warehouse_v1_suppliers.id", ondelete="SET NULL"),
        nullable=True,
    )
    quantity_on_hand: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quantity_reserved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    min_stock_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reorder_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<Part id={self.id} number={self.part_number} "
            f"on_hand={self.quantity_on_hand}>"
        )

    @property
    def quantity_available(self) -> int:
        return self.quantity_on_hand - self.quantity_reserved


class StockMovement(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "automotive_warehouse_v1_stock_movements"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_automotive_warehouse_v1_sm_qty"),
        Index("ix_automotive_warehouse_v1_sm_part_id", "part_id"),
        Index("ix_automotive_warehouse_v1_sm_movement_type", "movement_type"),
        Index("ix_automotive_warehouse_v1_sm_service_order_id", "service_order_id"),
    )

    part_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_warehouse_v1_parts.id", ondelete="CASCADE"),
        nullable=False,
    )
    movement_type: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    service_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_service_v1_service_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<StockMovement id={self.id} part={self.part_id} "
            f"type={self.movement_type} qty={self.quantity}>"
        )


class PartReservation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_warehouse_v1_reservations"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_automotive_warehouse_v1_res_qty"),
        Index("ix_automotive_warehouse_v1_res_part_id", "part_id"),
        Index("ix_automotive_warehouse_v1_res_service_order_id", "service_order_id"),
        Index("ix_automotive_warehouse_v1_res_status", "status"),
    )

    part_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_warehouse_v1_parts.id", ondelete="CASCADE"),
        nullable=False,
    )
    service_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_service_v1_service_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=PartReservationStatus.ACTIVE.value,
        nullable=False,
    )
    reserved_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<PartReservation id={self.id} part={self.part_id} "
            f"service_order={self.service_order_id}>"
        )


class ReorderRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_warehouse_v1_reorder_rules"
    __table_args__ = (
        UniqueConstraint("part_id", name="uq_automotive_warehouse_v1_reorder_rules_part_id"),
        CheckConstraint("min_quantity >= 0", name="ck_automotive_warehouse_v1_rr_min"),
        CheckConstraint("reorder_quantity > 0", name="ck_automotive_warehouse_v1_rr_reorder"),
        Index("ix_automotive_warehouse_v1_rr_supplier_id", "supplier_id"),
        Index("ix_automotive_warehouse_v1_rr_is_active", "is_active"),
    )

    part_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_warehouse_v1_parts.id", ondelete="CASCADE"),
        nullable=False,
    )
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_warehouse_v1_suppliers.id", ondelete="SET NULL"),
        nullable=True,
    )
    min_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reorder_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ReorderRule id={self.id} part={self.part_id} "
            f"min={self.min_quantity}>"
        )
