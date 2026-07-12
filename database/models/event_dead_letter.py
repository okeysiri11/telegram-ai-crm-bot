# Event Bus dead letter queue model.

from __future__ import annotations

from typing import Any

from sqlalchemy import Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class EventDeadLetter(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "event_dead_letters"
    __table_args__ = (
        Index("ix_event_dead_letters_event_name", "event_name"),
        Index("ix_event_dead_letters_created_at", "created_at"),
    )

    event_name: Mapped[str] = mapped_column(String(128), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<EventDeadLetter id={self.id} event={self.event_name} retries={self.retry_count}>"
