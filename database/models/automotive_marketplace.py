# Automotive Marketplace Connector Layer v1 — import jobs, logs, credentials.

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
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin

import database.models.automotive_inventory  # noqa: F401


class ConnectorType(str, enum.Enum):
    COPART = "COPART"
    IAAI = "IAAI"
    AUTORIA = "AUTORIA"
    OLX_AUTO = "OLX_AUTO"
    MOBILE_DE = "MOBILE_DE"
    LOCAL_DEALER = "LOCAL_DEALER"


class ImportJobStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ImportLogLevel(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ImportLogAction(str, enum.Enum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    SKIPPED_DUPLICATE = "SKIPPED_DUPLICATE"
    IMAGE_SYNCED = "IMAGE_SYNCED"
    PRICE_CHANGED = "PRICE_CHANGED"
    ERROR = "ERROR"


class ConnectorCredential(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_marketplace_v1_connector_credentials"
    __table_args__ = (
        UniqueConstraint(
            "connector_type",
            name="uq_automotive_marketplace_v1_credentials_connector_type",
        ),
        Index("ix_automotive_marketplace_v1_cred_is_active", "is_active"),
    )

    connector_type: Mapped[str] = mapped_column(String(30), nullable=False)
    api_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    api_secret: Mapped[str | None] = mapped_column(String(512), nullable=True)
    base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sync_interval_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<ConnectorCredential type={self.connector_type}>"


class VehicleImportJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_marketplace_v1_vehicle_import_jobs"
    __table_args__ = (
        Index("ix_automotive_marketplace_v1_job_connector", "connector_type"),
        Index("ix_automotive_marketplace_v1_job_status", "status"),
        Index("ix_automotive_marketplace_v1_job_scheduled_at", "scheduled_at"),
    )

    connector_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=ImportJobStatus.PENDING.value,
        nullable=False,
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    triggered_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_scheduled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    images_synced: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    price_changes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<VehicleImportJob id={self.id} connector={self.connector_type} "
            f"status={self.status}>"
        )


class VehicleImportLog(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "automotive_marketplace_v1_vehicle_import_logs"
    __table_args__ = (
        Index("ix_automotive_marketplace_v1_log_job_id", "job_id"),
        Index("ix_automotive_marketplace_v1_log_vin", "vin"),
        Index("ix_automotive_marketplace_v1_log_action", "action"),
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_marketplace_v1_vehicle_import_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    level: Mapped[str] = mapped_column(String(10), default=ImportLogLevel.INFO.value)
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vin: Mapped[str | None] = mapped_column(String(50), nullable=True)
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_v1_vehicles.id", ondelete="SET NULL"),
        nullable=True,
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    old_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    new_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)

    def __repr__(self) -> str:
        return f"<VehicleImportLog job={self.job_id} action={self.action}>"
