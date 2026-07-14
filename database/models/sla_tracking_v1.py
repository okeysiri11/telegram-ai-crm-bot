# SLA Tracking v1 — lead response and close-time metrics.

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class SlaTrafficLight(str, enum.Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


SLA_GREEN_MAX_MINUTES = 15
SLA_YELLOW_MAX_MINUTES = 60
SLA_OVERDUE_MINUTES = 15


class SlaTrackingV1Entry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sla_tracking_v1_entries"
    __table_args__ = (
        Index("ix_sla_tracking_v1_lead", "lead_id"),
        Index("ix_sla_tracking_v1_deal", "deal_id"),
        Index("ix_sla_tracking_v1_vertical", "vertical"),
        Index("ix_sla_tracking_v1_manager", "manager_id"),
        Index("ix_sla_tracking_v1_overdue", "is_overdue"),
        Index("ix_sla_tracking_v1_traffic", "response_traffic_light"),
        Index("ix_sla_tracking_v1_lead_created", "lead_created_at"),
    )

    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lead_engine_v1_leads.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    deal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deal_engine_v1_deals.id", ondelete="SET NULL"),
        nullable=True,
    )
    vertical: Mapped[str] = mapped_column(String(50), nullable=False)
    manager_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    lead_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    first_contact_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_response_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    manager_assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deal_closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    response_traffic_light: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_overdue: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    manager_telegram_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
