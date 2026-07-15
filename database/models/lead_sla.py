# Lead SLA metrics for CRM client_requests.

from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime
from datetime import datetime

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class LeadSlaRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "lead_sla_records"
    __table_args__ = (
        Index("ix_lead_sla_request", "client_request_id", unique=True),
        Index("ix_lead_sla_priority", "priority"),
        Index("ix_lead_sla_breached", "sla_breached"),
    )

    client_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("client_requests.id", ondelete="CASCADE"),
        nullable=False,
    )
    request_number: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at_lead: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    time_to_assignment_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_to_first_response_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_to_close_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)

    priority: Mapped[str] = mapped_column(String(16), default="MEDIUM", nullable=False)
    sla_breached: Mapped[bool] = mapped_column(default=False, nullable=False)
    escalation_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    manager_telegram_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
