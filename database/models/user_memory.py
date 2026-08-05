"""Telegram user memory (key/value profile facts) — PostgreSQL SoR."""

from __future__ import annotations

from sqlalchemy import BigInteger, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class UserMemory(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    """Canonical replacement for SQLite ``user_memory`` (database_legacy)."""

    __tablename__ = "user_memory"
    __table_args__ = (
        UniqueConstraint("telegram_id", "memory_key", name="uq_user_memory_telegram_key"),
        Index("ix_user_memory_telegram_id", "telegram_id"),
    )

    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    memory_key: Mapped[str] = mapped_column(String(64), nullable=False)
    memory_value: Mapped[str] = mapped_column(Text, nullable=False, default="")
