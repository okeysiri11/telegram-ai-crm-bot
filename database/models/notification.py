# Notification Engine model — outbound notification foundation.

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin

import database.models.deal  # noqa: F401 — register deal_engine_deals for FK resolution


class NotificationType(str, enum.Enum):
    DEAL_CREATED = "DEAL_CREATED"
    DEAL_ASSIGNED = "DEAL_ASSIGNED"
    STATUS_CHANGED = "STATUS_CHANGED"
    FUNDS_RECEIVED = "FUNDS_RECEIVED"
    DEAL_COMPLETED = "DEAL_COMPLETED"
    COMMISSION_CALCULATED = "COMMISSION_CALCULATED"
    COMMISSION_PAID = "COMMISSION_PAID"
    SYSTEM_ALERT = "SYSTEM_ALERT"


class NotificationChannel(str, enum.Enum):
    TELEGRAM = "TELEGRAM"
    EMAIL = "EMAIL"
    INTERNAL = "INTERNAL"


class NotificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class Notification(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "notification_engine_notifications"
    __table_args__ = (
        CheckConstraint("retries >= 0", name="ck_notification_engine_retries_non_negative"),
        Index("ix_notification_engine_user_id", "user_id"),
        Index("ix_notification_engine_deal_id", "deal_id"),
        Index("ix_notification_engine_status", "status"),
        Index("ix_notification_engine_notification_type", "notification_type"),
    )

    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    deal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deal_engine_deals.id", ondelete="SET NULL"),
        nullable=True,
    )
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(
        String(20),
        default=NotificationStatus.PENDING.value,
        nullable=False,
    )
    retries: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<Notification id={self.id} type={self.notification_type} "
            f"channel={self.channel} status={self.status}>"
        )
