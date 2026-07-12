# Automotive Sales Engine v1 — leads, reservations, test drives, pipeline.

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin

import database.models.automotive_inventory  # noqa: F401


class SalesPipelineStage(str, enum.Enum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    NEGOTIATION = "NEGOTIATION"
    RESERVED = "RESERVED"
    CONTRACT = "CONTRACT"
    PAID = "PAID"
    DELIVERED = "DELIVERED"


class LeadSource(str, enum.Enum):
    WEB = "WEB"
    PHONE = "PHONE"
    REFERRAL = "REFERRAL"
    WALK_IN = "WALK_IN"
    SOCIAL = "SOCIAL"
    OTHER = "OTHER"


class ReservationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CONVERTED = "CONVERTED"
    CANCELLED = "CANCELLED"


class TestDriveStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class Lead(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_sales_v1_leads"
    __table_args__ = (
        Index("ix_automotive_sales_v1_leads_pipeline_stage", "pipeline_stage"),
        Index("ix_automotive_sales_v1_leads_vehicle_id", "vehicle_id"),
        Index("ix_automotive_sales_v1_leads_assigned_to", "assigned_to"),
    )

    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_v1_vehicles.id", ondelete="SET NULL"),
        nullable=True,
    )
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    customer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str] = mapped_column(
        String(30),
        default=LeadSource.OTHER.value,
        nullable=False,
    )
    pipeline_stage: Mapped[str] = mapped_column(
        String(30),
        default=SalesPipelineStage.NEW.value,
        nullable=False,
    )
    assigned_to: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    budget: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<Lead id={self.id} name={self.customer_name} "
            f"stage={self.pipeline_stage}>"
        )


class VehicleReservation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_sales_v1_vehicle_reservations"
    __table_args__ = (
        Index("ix_automotive_sales_v1_res_lead_id", "lead_id"),
        Index("ix_automotive_sales_v1_res_vehicle_id", "vehicle_id"),
        Index("ix_automotive_sales_v1_res_status", "status"),
    )

    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_sales_v1_leads.id", ondelete="CASCADE"),
        nullable=False,
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_v1_vehicles.id", ondelete="CASCADE"),
        nullable=False,
    )
    reserved_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    deposit_amount: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=ReservationStatus.ACTIVE.value,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<VehicleReservation id={self.id} lead={self.lead_id} "
            f"vehicle={self.vehicle_id}>"
        )


class TestDrive(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_sales_v1_test_drives"
    __table_args__ = (
        Index("ix_automotive_sales_v1_td_lead_id", "lead_id"),
        Index("ix_automotive_sales_v1_td_vehicle_id", "vehicle_id"),
        Index("ix_automotive_sales_v1_td_status", "status"),
        Index("ix_automotive_sales_v1_td_scheduled_at", "scheduled_at"),
    )

    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_sales_v1_leads.id", ondelete="CASCADE"),
        nullable=False,
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_v1_vehicles.id", ondelete="CASCADE"),
        nullable=False,
    )
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=TestDriveStatus.SCHEDULED.value,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<TestDrive id={self.id} lead={self.lead_id} "
            f"scheduled={self.scheduled_at}>"
        )


class SalesPipelineEntry(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "automotive_sales_v1_sales_pipeline"
    __table_args__ = (
        Index("ix_automotive_sales_v1_sp_lead_id", "lead_id"),
        Index("ix_automotive_sales_v1_sp_to_stage", "to_stage"),
    )

    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_sales_v1_leads.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_stage: Mapped[str | None] = mapped_column(String(30), nullable=True)
    to_stage: Mapped[str] = mapped_column(String(30), nullable=False)
    changed_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<SalesPipelineEntry lead={self.lead_id} "
            f"{self.from_stage}->{self.to_stage}>"
        )
