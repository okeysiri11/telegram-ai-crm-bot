# manager_pool ORM — dynamic manager assignment pool.

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ManagerPoolEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "manager_pool"
    __table_args__ = (
        UniqueConstraint("telegram_id", "vertical", name="uq_manager_pool_telegram_vertical"),
        Index("ix_manager_pool_vertical", "vertical"),
        Index("ix_manager_pool_is_active", "is_active"),
        Index("ix_manager_pool_priority", "priority"),
        Index("ix_manager_pool_current_load", "current_load"),
        Index("ix_manager_pool_last_assigned_at", "last_assigned_at"),
    )

    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    vertical: Mapped[str] = mapped_column(String(32), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    weight: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    current_load: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
