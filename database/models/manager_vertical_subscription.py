# Manager vertical subscriptions — which managers receive which vertical leads.

from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ManagerVerticalSubscription(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Subscription of a manager user to one or more verticals."""

    __tablename__ = "manager_vertical_subscriptions_v1"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "vertical",
            name="uq_manager_vertical_subscriptions_v1_user_vertical",
        ),
        Index("ix_manager_vertical_subscriptions_v1_vertical", "vertical"),
        Index("ix_manager_vertical_subscriptions_v1_telegram", "telegram_user_id"),
        Index("ix_manager_vertical_subscriptions_v1_active", "is_active"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    vertical: Mapped[str] = mapped_column(String(32), nullable=False)
    role_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
