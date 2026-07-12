# Calendar event models.

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from database.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from database.models.tasks import Task
    from database.models.users import User


class CalendarEvent(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "calendar_events"
    __table_args__ = (
        Index("ix_calendar_events_module", "module"),
        Index("ix_calendar_events_owner_id", "owner_id"),
        Index("ix_calendar_events_creator_id", "creator_id"),
        Index("ix_calendar_events_department", "department"),
        Index("ix_calendar_events_visibility", "visibility"),
        Index("ix_calendar_events_start", "start_datetime"),
        Index("ix_calendar_events_status", "status"),
        Index("ix_calendar_events_public_id", "public_id", unique=True),
    )

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    module: Mapped[str] = mapped_column(String(64), default="system", nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), default="general", nullable=False)
    creator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False,
    )
    assigned_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    responsible_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    start_time: Mapped[str | None] = mapped_column(String(32), nullable=True)
    end_time: Mapped[str | None] = mapped_column(String(32), nullable=True)
    start_datetime: Mapped[datetime | None] = mapped_column(nullable=True)
    end_datetime: Mapped[datetime | None] = mapped_column(nullable=True)
    remind_before: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reminder_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    repeat_rule: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="PLANNED", nullable=False)
    priority: Mapped[str] = mapped_column(String(32), default="normal", nullable=False)
    department: Mapped[str | None] = mapped_column(String(64), nullable=True)
    visibility: Mapped[str] = mapped_column(String(32), default="DEPARTMENT", nullable=False)
    public_id: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)

    creator: Mapped[User] = relationship(foreign_keys=[creator_id])
    owner: Mapped[User] = relationship(foreign_keys=[owner_id])
    tasks: Mapped[list[Task]] = relationship(back_populates="calendar_event")
