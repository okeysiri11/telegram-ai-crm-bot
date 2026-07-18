# Platform configuration ORM — centralized settings with versioning.

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PlatformConfigEntry(Base):
    __tablename__ = "platform_config"
    __table_args__ = (
        Index("ix_platform_config_section", "section"),
        Index("ix_platform_config_version", "version"),
    )

    key: Mapped[str] = mapped_column(String(256), primary_key=True)
    section: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSONB, nullable=True)
    value_type: Mapped[str] = mapped_column(String(32), nullable=False, default="json")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class PlatformConfigHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "platform_config_history"
    __table_args__ = (
        UniqueConstraint("config_key", "version", name="uq_platform_config_history_key_version"),
        Index("ix_platform_config_history_config_key", "config_key"),
        Index("ix_platform_config_history_changed_at", "changed_at"),
    )

    config_key: Mapped[str] = mapped_column(String(256), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    old_value: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSONB, nullable=True)
    action: Mapped[str] = mapped_column(String(32), nullable=False, default="set")
    changed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
