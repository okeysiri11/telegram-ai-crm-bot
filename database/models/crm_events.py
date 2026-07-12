# CRM Event Bus persistence model — PostgreSQL.

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import UUIDPrimaryKeyMixin

EVENT_STATUS_PENDING = "PENDING"
EVENT_STATUS_PROCESSING = "PROCESSING"
EVENT_STATUS_COMPLETED = "COMPLETED"
EVENT_STATUS_FAILED = "FAILED"
EVENT_STATUS_DEAD_LETTER = "DEAD_LETTER"

EVENT_STATUSES = (
    EVENT_STATUS_PENDING,
    EVENT_STATUS_PROCESSING,
    EVENT_STATUS_COMPLETED,
    EVENT_STATUS_FAILED,
    EVENT_STATUS_DEAD_LETTER,
)


class Event(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_event_type", "event_type"),
        Index("ix_events_aggregate_id", "aggregate_id"),
        Index("ix_events_correlation_id", "correlation_id"),
        Index("ix_events_status", "status"),
        Index("ix_events_created_at", "created_at"),
        UniqueConstraint(
            "event_type",
            "aggregate_type",
            "aggregate_id",
            "correlation_id",
            name="uq_events_idempotency",
        ),
    )

    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(128), nullable=False)
    aggregate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    correlation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    causation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default=EVENT_STATUS_PENDING,
        nullable=False,
    )
    delivery_state: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<Event id={self.id} type={self.event_type} "
            f"aggregate={self.aggregate_type}:{self.aggregate_id} status={self.status}>"
        )
