# AI Sales Assistant v1 — customer conversations, financing, meetings, handoffs.

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class SalesSessionStatus(str, enum.Enum):
    ACTIVE = "active"
    COLLECTING_CONTACT = "collecting_contact"
    SCHEDULING_MEETING = "scheduling_meeting"
    TRANSFERRED = "transferred"
    CLOSED = "closed"


class SalesMessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SalesMeetingStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SalesHandoffStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    CLOSED = "closed"


SALES_SESSION_STATUSES = frozenset(s.value for s in SalesSessionStatus)
SALES_MESSAGE_ROLES = frozenset(r.value for r in SalesMessageRole)
SALES_MEETING_STATUSES = frozenset(s.value for s in SalesMeetingStatus)
SALES_HANDOFF_STATUSES = frozenset(s.value for s in SalesHandoffStatus)


class SalesAssistantSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_sales_assistant_v1_sessions"
    __table_args__ = (
        Index("ix_ai_sales_assistant_v1_sessions_telegram", "telegram_user_id"),
        Index("ix_ai_sales_assistant_v1_sessions_status", "status"),
        Index("ix_ai_sales_assistant_v1_sessions_lead", "lead_id"),
        Index("ix_ai_sales_assistant_v1_sessions_car", "car_id"),
        Index("ix_ai_sales_assistant_v1_sessions_manager", "assigned_manager_id"),
    )

    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    lead_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    car_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("car_engine_v1_cars.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default=SalesSessionStatus.ACTIVE.value,
        nullable=False,
    )
    contact_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    financing_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scheduling_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    assigned_manager_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_intent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<SalesAssistantSession telegram={self.telegram_user_id} "
            f"status={self.status}>"
        )


class SalesAssistantMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_sales_assistant_v1_messages"
    __table_args__ = (
        Index("ix_ai_sales_assistant_v1_messages_session", "session_id"),
        Index("ix_ai_sales_assistant_v1_messages_role", "role"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_sales_assistant_v1_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<SalesAssistantMessage session={self.session_id} role={self.role}>"


class SalesAssistantMeeting(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_sales_assistant_v1_meetings"
    __table_args__ = (
        Index("ix_ai_sales_assistant_v1_meetings_session", "session_id"),
        Index("ix_ai_sales_assistant_v1_meetings_status", "status"),
        Index("ix_ai_sales_assistant_v1_meetings_scheduled", "scheduled_at"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_sales_assistant_v1_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    calendar_event_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30),
        default=SalesMeetingStatus.SCHEDULED.value,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<SalesAssistantMeeting session={self.session_id} at={self.scheduled_at}>"


class SalesAssistantHandoff(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_sales_assistant_v1_handoffs"
    __table_args__ = (
        Index("ix_ai_sales_assistant_v1_handoffs_session", "session_id"),
        Index("ix_ai_sales_assistant_v1_handoffs_manager", "manager_id"),
        Index("ix_ai_sales_assistant_v1_handoffs_status", "status"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_sales_assistant_v1_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    manager_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30),
        default=SalesHandoffStatus.PENDING.value,
        nullable=False,
    )
    transferred_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<SalesAssistantHandoff session={self.session_id} manager={self.manager_id}>"
