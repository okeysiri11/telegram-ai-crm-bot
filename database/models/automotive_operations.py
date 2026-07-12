# Automotive Operations Engine v1 — vehicle lifecycle workflow.

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin

import database.models.automotive_inventory  # noqa: F401


class VehicleOperationState(str, enum.Enum):
    PROCUREMENT = "PROCUREMENT"
    IN_TRANSIT = "IN_TRANSIT"
    CUSTOMS = "CUSTOMS"
    WAREHOUSE = "WAREHOUSE"
    PREPARATION = "PREPARATION"
    LISTED_FOR_SALE = "LISTED_FOR_SALE"
    RESERVED = "RESERVED"
    SOLD = "SOLD"
    DELIVERED = "DELIVERED"
    CLOSED = "CLOSED"


class VehicleTaskType(str, enum.Enum):
    LOGISTICS_ORDER = "LOGISTICS_ORDER"
    TREASURY_RESERVE = "TREASURY_RESERVE"
    CUSTOMS_CLEARANCE = "CUSTOMS_CLEARANCE"
    INSPECTION = "INSPECTION"
    DETAILING = "DETAILING"
    PHOTOGRAPHY = "PHOTOGRAPHY"
    MARKETPLACE_PUBLISH = "MARKETPLACE_PUBLISH"
    SALES_NOTIFY = "SALES_NOTIFY"
    SETTLEMENT = "SETTLEMENT"
    DELIVERY = "DELIVERY"
    RELEASE_RESERVATION = "RELEASE_RESERVATION"
    ACCOUNTING_ENTRY = "ACCOUNTING_ENTRY"


class VehicleTaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    OVERDUE = "OVERDUE"


class VehicleTaskPriority(str, enum.Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class VehicleAttachmentType(str, enum.Enum):
    PHOTO = "PHOTO"
    DOCUMENT = "DOCUMENT"
    INSPECTION_REPORT = "INSPECTION_REPORT"
    CONTRACT = "CONTRACT"
    OTHER = "OTHER"


class VehicleOperation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_operations_v1_vehicle_operations"
    __table_args__ = (
        UniqueConstraint(
            "vehicle_id",
            name="uq_automotive_operations_v1_ops_vehicle_id",
        ),
        Index("ix_automotive_operations_v1_ops_state", "current_state"),
        Index("ix_automotive_operations_v1_ops_manager", "assigned_manager_id"),
        Index("ix_automotive_operations_v1_ops_sla", "sla_deadline"),
    )

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_v1_vehicles.id", ondelete="CASCADE"),
        nullable=False,
    )
    current_state: Mapped[str] = mapped_column(
        String(30),
        default=VehicleOperationState.PROCUREMENT.value,
        nullable=False,
    )
    assigned_manager_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    state_entered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    sla_deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<VehicleOperation vehicle={self.vehicle_id} "
            f"state={self.current_state}>"
        )


class VehicleStateHistory(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "automotive_operations_v1_vehicle_state_history"
    __table_args__ = (
        Index("ix_automotive_operations_v1_state_hist_operation", "operation_id"),
        Index("ix_automotive_operations_v1_state_hist_vehicle", "vehicle_id"),
    )

    operation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_operations_v1_vehicle_operations.id", ondelete="CASCADE"),
        nullable=False,
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_v1_vehicles.id", ondelete="CASCADE"),
        nullable=False,
    )
    from_state: Mapped[str | None] = mapped_column(String(30), nullable=True)
    to_state: Mapped[str] = mapped_column(String(30), nullable=False)
    changed_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<VehicleStateHistory op={self.operation_id} "
            f"{self.from_state}->{self.to_state}>"
        )


class VehicleTask(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_operations_v1_vehicle_tasks"
    __table_args__ = (
        Index("ix_automotive_operations_v1_tasks_operation", "operation_id"),
        Index("ix_automotive_operations_v1_tasks_vehicle", "vehicle_id"),
        Index("ix_automotive_operations_v1_tasks_status", "status"),
        Index("ix_automotive_operations_v1_tasks_assigned", "assigned_to"),
        Index("ix_automotive_operations_v1_tasks_sla", "sla_deadline"),
        Index("ix_automotive_operations_v1_tasks_type", "task_type"),
    )

    operation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_operations_v1_vehicle_operations.id", ondelete="CASCADE"),
        nullable=False,
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_v1_vehicles.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=VehicleTaskStatus.PENDING.value,
        nullable=False,
    )
    priority: Mapped[str] = mapped_column(
        String(10),
        default=VehicleTaskPriority.NORMAL.value,
        nullable=False,
    )
    assigned_to: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    sla_deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    auto_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<VehicleTask type={self.task_type} status={self.status}>"


class VehicleChecklist(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_operations_v1_vehicle_checklists"
    __table_args__ = (
        Index("ix_automotive_operations_v1_checklists_operation", "operation_id"),
        Index("ix_automotive_operations_v1_checklists_task", "task_id"),
    )

    operation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_operations_v1_vehicle_operations.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_operations_v1_vehicle_tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    item_key: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<VehicleChecklist key={self.item_key} done={self.is_completed}>"


class VehicleAttachment(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "automotive_operations_v1_vehicle_attachments"
    __table_args__ = (
        Index("ix_automotive_operations_v1_attachments_operation", "operation_id"),
        Index("ix_automotive_operations_v1_attachments_vehicle", "vehicle_id"),
        Index("ix_automotive_operations_v1_attachments_task", "task_id"),
    )

    operation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_operations_v1_vehicle_operations.id", ondelete="CASCADE"),
        nullable=False,
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_v1_vehicles.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_operations_v1_vehicle_tasks.id", ondelete="SET NULL"),
        nullable=True,
    )
    file_url: Mapped[str] = mapped_column(String(512), nullable=False)
    attachment_type: Mapped[str] = mapped_column(String(30), nullable=False)
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    uploaded_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<VehicleAttachment type={self.attachment_type} url={self.file_url}>"
