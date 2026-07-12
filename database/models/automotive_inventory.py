# Automotive Inventory Engine v1 — vehicles, images, documents, status, locations.

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
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin


class VehicleStatus(str, enum.Enum):
    IN_TRANSIT = "IN_TRANSIT"
    IN_CUSTOMS = "IN_CUSTOMS"
    AT_PORT = "AT_PORT"
    IN_STOCK = "IN_STOCK"
    RESERVED = "RESERVED"
    SOLD = "SOLD"
    DELIVERED = "DELIVERED"


class VehicleDocumentStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class Vehicle(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_v1_vehicles"
    __table_args__ = (
        UniqueConstraint("vin", name="uq_automotive_v1_vehicles_vin"),
        UniqueConstraint("stock_number", name="uq_automotive_v1_vehicles_stock_number"),
        CheckConstraint("year >= 1900", name="ck_automotive_v1_vehicles_year"),
        CheckConstraint("mileage >= 0", name="ck_automotive_v1_vehicles_mileage"),
        Index("ix_automotive_v1_vehicles_status", "status"),
        Index("ix_automotive_v1_vehicles_make_model", "make", "model"),
        Index("ix_automotive_v1_vehicles_year", "year"),
    )

    vin: Mapped[str] = mapped_column(String(50), nullable=False)
    stock_number: Mapped[str] = mapped_column(String(50), nullable=False)
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    generation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    engine: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fuel_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    transmission: Mapped[str | None] = mapped_column(String(50), nullable=True)
    drivetrain: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mileage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    purchase_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    target_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    sale_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=VehicleStatus.IN_TRANSIT.value,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<Vehicle id={self.id} {self.year} {self.make} {self.model} "
            f"status={self.status}>"
        )


class VehicleImage(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "automotive_v1_vehicle_images"
    __table_args__ = (
        Index("ix_automotive_v1_vehicle_images_vehicle_id", "vehicle_id"),
        Index("ix_automotive_v1_vehicle_images_sort_order", "sort_order"),
    )

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_v1_vehicles.id", ondelete="CASCADE"),
        nullable=False,
    )
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    image_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    caption: Mapped[str | None] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<VehicleImage id={self.id} vehicle={self.vehicle_id} type={self.image_type}>"


class VehicleDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_v1_vehicle_documents"
    __table_args__ = (
        Index("ix_automotive_v1_vehicle_documents_vehicle_id", "vehicle_id"),
        Index("ix_automotive_v1_vehicle_documents_document_type", "document_type"),
        Index("ix_automotive_v1_vehicle_documents_status", "status"),
    )

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_v1_vehicles.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_url: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=VehicleDocumentStatus.PENDING.value,
        nullable=False,
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<VehicleDocument id={self.id} vehicle={self.vehicle_id} "
            f"type={self.document_type}>"
        )


class VehicleStatusHistory(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "automotive_v1_status_history"
    __table_args__ = (
        Index("ix_automotive_v1_status_history_vehicle_id", "vehicle_id"),
        Index("ix_automotive_v1_status_history_to_status", "to_status"),
    )

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_v1_vehicles.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    to_status: Mapped[str] = mapped_column(String(30), nullable=False)
    changed_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<VehicleStatusHistory vehicle={self.vehicle_id} "
            f"{self.from_status}->{self.to_status}>"
        )


class VehicleLocation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_v1_vehicle_locations"
    __table_args__ = (
        Index("ix_automotive_v1_vehicle_locations_vehicle_id", "vehicle_id"),
        Index("ix_automotive_v1_vehicle_locations_is_current", "is_current"),
        Index("ix_automotive_v1_vehicle_locations_location_type", "location_type"),
    )

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_v1_vehicles.id", ondelete="CASCADE"),
        nullable=False,
    )
    location_type: Mapped[str] = mapped_column(String(50), nullable=False)
    location_name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    arrived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    departed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<VehicleLocation id={self.id} vehicle={self.vehicle_id} "
            f"name={self.location_name} current={self.is_current}>"
        )
