# Platform event bus models.

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from database.models.users import User


class PlatformEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "platform_events"
    __table_args__ = (
        Index("ix_platform_events_type", "event_type"),
        Index("ix_platform_events_module", "module"),
        Index("ix_platform_events_entity", "entity_type", "entity_id"),
        Index("ix_platform_events_user_id", "user_id"),
        Index("ix_platform_events_status", "status"),
        Index("ix_platform_events_created_at", "created_at"),
    )

    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    module: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="PUBLISHED", nullable=False)
    delivery_errors: Mapped[str | None] = mapped_column(Text, nullable=True)
    replay_of_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("platform_events.id", ondelete="SET NULL"),
        nullable=True,
    )

    user: Mapped[User] = relationship(foreign_keys=[user_id])
    replay_of: Mapped[PlatformEvent | None] = relationship(
        remote_side="PlatformEvent.id",
        foreign_keys=[replay_of_id],
    )
