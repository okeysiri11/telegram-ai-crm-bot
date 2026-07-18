# request_sla ORM — per-request SLA tracking for escalation engine.

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, SmallInteger, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class RequestSla(Base):
    __tablename__ = "request_sla"
    __table_args__ = (
        Index("ix_request_sla_manager_id", "manager_id"),
        Index("ix_request_sla_first_response_deadline", "first_response_deadline"),
        Index("ix_request_sla_escalation_level", "escalation_level"),
        Index("ix_request_sla_first_response_at", "first_response_at"),
        Index("ix_request_sla_completed_at", "completed_at"),
    )

    request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    manager_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    first_response_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completion_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    escalation_level: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    first_response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
