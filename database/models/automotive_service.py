# Automotive Service Engine v1 — orders, operations, parts, history, warranty.

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
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

import database.models.automotive_inventory  # noqa: F401


class ServiceOrderStatus(str, enum.Enum):
    CREATED = "CREATED"
    DIAGNOSIS = "DIAGNOSIS"
    WAITING_PARTS = "WAITING_PARTS"
    IN_PROGRESS = "IN_PROGRESS"
    READY = "READY"
    DELIVERED = "DELIVERED"
    CLOSED = "CLOSED"


class OperationType(str, enum.Enum):
    ENGINE = "ENGINE"
    SUSPENSION = "SUSPENSION"
    BODYWORK = "BODYWORK"
    PAINT = "PAINT"
    DETAILING = "DETAILING"
    DIAGNOSTICS = "DIAGNOSTICS"
    ELECTRICS = "ELECTRICS"
    OTHER = "OTHER"


class ServiceOperationStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class WarrantyStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    VOID = "VOID"


class WarrantyType(str, enum.Enum):
    PARTS = "PARTS"
    LABOR = "LABOR"
    FULL = "FULL"


class ServiceOrder(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_service_v1_service_orders"
    __table_args__ = (
        UniqueConstraint(
            "order_number",
            name="uq_automotive_service_v1_service_orders_order_number",
        ),
        CheckConstraint("labor_total >= 0", name="ck_automotive_service_v1_so_labor"),
        CheckConstraint("parts_total >= 0", name="ck_automotive_service_v1_so_parts"),
        CheckConstraint("total_cost >= 0", name="ck_automotive_service_v1_so_total"),
        Index("ix_automotive_service_v1_so_status", "status"),
        Index("ix_automotive_service_v1_so_vehicle_id", "vehicle_id"),
    )

    order_number: Mapped[str] = mapped_column(String(50), nullable=False)
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_v1_vehicles.id", ondelete="CASCADE"),
        nullable=False,
    )
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30),
        default=ServiceOrderStatus.CREATED.value,
        nullable=False,
    )
    assigned_to: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    labor_total: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0"),
        nullable=False,
    )
    parts_total: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0"),
        nullable=False,
    )
    total_cost: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        default=Decimal("0"),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    diagnosis_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ServiceOrder id={self.id} number={self.order_number} "
            f"status={self.status}>"
        )


class ServiceOperation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_service_v1_service_operations"
    __table_args__ = (
        CheckConstraint("labor_hours >= 0", name="ck_automotive_service_v1_op_hours"),
        CheckConstraint("labor_cost >= 0", name="ck_automotive_service_v1_op_cost"),
        Index("ix_automotive_service_v1_op_order_id", "service_order_id"),
        Index("ix_automotive_service_v1_op_type", "operation_type"),
        Index("ix_automotive_service_v1_op_status", "status"),
    )

    service_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_service_v1_service_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    operation_type: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    labor_hours: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        default=Decimal("0"),
        nullable=False,
    )
    labor_rate: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    labor_cost: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    technician_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default=ServiceOperationStatus.PENDING.value,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ServiceOperation id={self.id} type={self.operation_type} "
            f"cost={self.labor_cost}>"
        )


class ServicePart(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_service_v1_service_parts"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_automotive_service_v1_part_qty"),
        CheckConstraint("total_price >= 0", name="ck_automotive_service_v1_part_total"),
        Index("ix_automotive_service_v1_part_order_id", "service_order_id"),
        Index("ix_automotive_service_v1_part_operation_id", "service_operation_id"),
    )

    service_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_service_v1_service_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    service_operation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_service_v1_service_operations.id", ondelete="SET NULL"),
        nullable=True,
    )
    part_number: Mapped[str] = mapped_column(String(100), nullable=False)
    part_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ServicePart id={self.id} number={self.part_number} "
            f"qty={self.quantity}>"
        )


class ServiceHistory(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "automotive_service_v1_service_history"
    __table_args__ = (
        Index("ix_automotive_service_v1_sh_order_id", "service_order_id"),
        Index("ix_automotive_service_v1_sh_to_status", "to_status"),
    )

    service_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_service_v1_service_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    to_status: Mapped[str] = mapped_column(String(30), nullable=False)
    changed_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ServiceHistory order={self.service_order_id} "
            f"{self.from_status}->{self.to_status}>"
        )


class WarrantyRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_service_v1_warranty_records"
    __table_args__ = (
        Index("ix_automotive_service_v1_wr_vehicle_id", "vehicle_id"),
        Index("ix_automotive_service_v1_wr_order_id", "service_order_id"),
        Index("ix_automotive_service_v1_wr_status", "status"),
        Index("ix_automotive_service_v1_wr_expires_at", "expires_at"),
    )

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_v1_vehicles.id", ondelete="CASCADE"),
        nullable=False,
    )
    service_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_service_v1_service_orders.id", ondelete="SET NULL"),
        nullable=True,
    )
    warranty_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=WarrantyStatus.ACTIVE.value,
        nullable=False,
    )
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    mileage_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    coverage_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<WarrantyRecord id={self.id} vehicle={self.vehicle_id} "
            f"type={self.warranty_type}>"
        )
