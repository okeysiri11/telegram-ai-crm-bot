# ORM model — platform audit_events table.

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import UUIDPrimaryKeyMixin


class AuditEventRow(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_created_at", "created_at"),
        Index("ix_audit_events_entity", "entity_type", "entity_id"),
        Index("ix_audit_events_event_type", "event_type"),
        Index("ix_audit_events_actor_id", "actor_id"),
        Index(
            "ix_audit_events_metadata_manager_id",
            "metadata_json",
            postgresql_using="gin",
            postgresql_ops={"metadata_json": "jsonb_path_ops"},
        ),
    )

    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    old_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<AuditEventRow type={self.event_type} entity={self.entity_id}>"
