# Platform audit log — CRM / marketplace action trail.

from __future__ import annotations

import enum
import logging
import uuid
from typing import Any

from sqlalchemy import BigInteger, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin

logger = logging.getLogger(__name__)


class PlatformAuditEvent(str, enum.Enum):
    LEAD_CREATED = "LEAD_CREATED"
    STATUS_CHANGED = "STATUS_CHANGED"
    MANAGER_ASSIGNED = "MANAGER_ASSIGNED"
    DEAL_OWNER_CHANGED = "DEAL_OWNER_CHANGED"
    CLIENT_DATA_UPDATED = "CLIENT_DATA_UPDATED"
    ADMIN_LOGIN = "ADMIN_LOGIN"
    AI_ACTION = "AI_ACTION"
    SLA_VIOLATION = "SLA_VIOLATION"
    ESCALATION = "ESCALATION"
    INVENTORY_CREATED = "INVENTORY_CREATED"
    INVENTORY_UPDATED = "INVENTORY_UPDATED"
    NOTIFICATION_SENT = "NOTIFICATION_SENT"


class PlatformAuditLog(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "audit_log"
    __table_args__ = (
        Index("ix_audit_log_event_type", "event_type"),
        Index("ix_audit_log_entity", "entity_type", "entity_id"),
        Index("ix_audit_log_user_id", "user_id"),
        Index("ix_audit_log_created_at", "created_at"),
    )

    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False)
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
