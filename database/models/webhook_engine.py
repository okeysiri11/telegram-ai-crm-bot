# Webhook Engine v1 — subscriptions, deliveries, failures, retries.

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
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
from database.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin


class WebhookSubscriptionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    REVOKED = "REVOKED"


class WebhookDeliveryStatus(str, enum.Enum):
    PENDING = "PENDING"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    DEAD_LETTER = "DEAD_LETTER"


class WebhookRetryStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    DEAD_LETTER = "DEAD_LETTER"
    CANCELLED = "CANCELLED"


class WebhookSubscription(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "webhook_engine_v1_webhook_subscriptions"
    __table_args__ = (
        Index("ix_webhook_engine_v1_sub_status", "status"),
        Index("ix_webhook_engine_v1_sub_owner", "owner_user_id"),
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    target_url: Mapped[str] = mapped_column(String(512), nullable=False)
    secret: Mapped[str] = mapped_column(String(128), nullable=False)
    event_types: Mapped[list] = mapped_column(JSONB, nullable=False)
    event_version: Mapped[str] = mapped_column(String(10), default="v1", nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=WebhookSubscriptionStatus.ACTIVE.value,
        nullable=False,
    )
    owner_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<WebhookSubscription name={self.name} url={self.target_url}>"


class WebhookDelivery(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "webhook_engine_v1_webhook_deliveries"
    __table_args__ = (
        Index("ix_webhook_engine_v1_del_subscription", "subscription_id"),
        Index("ix_webhook_engine_v1_del_status", "status"),
        Index("ix_webhook_engine_v1_del_event_type", "event_type"),
        Index("ix_webhook_engine_v1_del_source_event", "source_event_id"),
    )

    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("webhook_engine_v1_webhook_subscriptions.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_event_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    event_version: Mapped[str] = mapped_column(String(10), default="v1", nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    signature: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default=WebhookDeliveryStatus.PENDING.value,
        nullable=False,
    )
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<WebhookDelivery sub={self.subscription_id} "
            f"type={self.event_type} status={self.status}>"
        )


class WebhookFailure(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "webhook_engine_v1_webhook_failures"
    __table_args__ = (
        Index("ix_webhook_engine_v1_fail_delivery", "delivery_id"),
        Index("ix_webhook_engine_v1_fail_subscription", "subscription_id"),
    )

    delivery_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("webhook_engine_v1_webhook_deliveries.id", ondelete="CASCADE"),
        nullable=False,
    )
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("webhook_engine_v1_webhook_subscriptions.id", ondelete="CASCADE"),
        nullable=False,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_terminal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<WebhookFailure delivery={self.delivery_id} attempt={self.attempt_number}>"


class WebhookRetry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "webhook_engine_v1_webhook_retries"
    __table_args__ = (
        Index("ix_webhook_engine_v1_retry_delivery", "delivery_id"),
        Index("ix_webhook_engine_v1_retry_scheduled", "scheduled_at"),
        Index("ix_webhook_engine_v1_retry_status", "status"),
    )

    delivery_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("webhook_engine_v1_webhook_deliveries.id", ondelete="CASCADE"),
        nullable=False,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=WebhookRetryStatus.PENDING.value,
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<WebhookRetry delivery={self.delivery_id} attempt={self.attempt_number}>"
