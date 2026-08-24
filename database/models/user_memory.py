"""Telegram user memory (key/value profile facts) — PostgreSQL SoR."""

from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class UserMemory(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    """Canonical replacement for SQLite ``user_memory`` (database_legacy)."""

    __tablename__ = "user_memory"
    __table_args__ = (
        UniqueConstraint("telegram_id", "memory_key", name="uq_user_memory_telegram_key"),
        Index("ix_user_memory_telegram_id", "telegram_id"),
        Index("ix_user_memory_tenant_id", "tenant_id"),
    )

    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    memory_key: Mapped[str] = mapped_column(String(64), nullable=False)
    memory_value: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Sprint 47.1 — AI Agent Memory Architecture scope columns (nullable/
    # additive, see migrations/versions/v5p678901234_memory_scope_47_1.py and
    # platform_memory.scope.MemoryScope). tenant_id is the canonical org
    # identifier (Sprint 47.0 Decision 5).
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="SET NULL"),
        nullable=True,
    )
    vertical: Mapped[str | None] = mapped_column(String(64), nullable=True)
    customer_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
