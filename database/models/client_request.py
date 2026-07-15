# Unified client request CRM records (history, pipeline, funnel).

from __future__ import annotations

import enum
import uuid

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ClientRequestStatus(str, enum.Enum):
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_CLIENT = "WAITING_CLIENT"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class CrmFunnelStage(str, enum.Enum):
    NEW_LEAD = "NEW_LEAD"
    CONTACTED = "CONTACTED"
    NEGOTIATION = "NEGOTIATION"
    PROPOSAL = "PROPOSAL"
    DEAL = "DEAL"
    CLOSED = "CLOSED"
    LOST = "LOST"


class ClientRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "client_requests"
    __table_args__ = (
        Index("ix_client_requests_client", "client_telegram_id"),
        Index("ix_client_requests_manager", "manager_id"),
        Index("ix_client_requests_status", "status"),
        Index("ix_client_requests_funnel", "funnel_stage"),
        Index("ix_client_requests_type", "request_type"),
        Index("ix_client_requests_number", "request_number", unique=True),
    )

    request_number: Mapped[str] = mapped_column(String(32), nullable=False)
    request_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default=ClientRequestStatus.NEW.value,
        nullable=False,
    )
    funnel_stage: Mapped[str] = mapped_column(
        String(32),
        default=CrmFunnelStage.NEW_LEAD.value,
        nullable=False,
    )

    client_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    client_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    client_language_code: Mapped[str | None] = mapped_column(String(8), nullable=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    vin: Mapped[str | None] = mapped_column(String(17), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mileage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    budget: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    price: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    fuel: Mapped[str | None] = mapped_column(String(64), nullable=True)
    engine: Mapped[str | None] = mapped_column(String(64), nullable=True)
    transmission: Mapped[str | None] = mapped_column(String(64), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    service_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    photo_file_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    ai_qualification: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    manager_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    auto_request_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auto_client_requests_v1.id", ondelete="SET NULL"),
        nullable=True,
    )
    marketplace_listing_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("marketplace_listings.id", ondelete="SET NULL"),
        nullable=True,
    )
