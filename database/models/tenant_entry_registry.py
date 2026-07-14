# Tenant entry link registry and owner vertical notes.

from __future__ import annotations

from sqlalchemy import Boolean, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class TenantEntryLink(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenant_entry_links_v1"
    __table_args__ = (
        Index("ix_tenant_entry_links_code", "code", unique=True),
        Index("ix_tenant_entry_links_tenant", "tenant_code"),
        Index("ix_tenant_entry_links_active", "is_active"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    tenant_code: Mapped[str] = mapped_column(String(64), nullable=False)
    vertical: Mapped[str] = mapped_column(String(32), nullable=False)
    title_ru: Mapped[str] = mapped_column(String(128), nullable=False)
    title_uk: Mapped[str] = mapped_column(String(128), nullable=False)
    preset_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entry_target: Mapped[str | None] = mapped_column(String(64), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class OwnerVerticalNote(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "owner_vertical_notes_v1"
    __table_args__ = (
        Index("ix_owner_notes_vertical", "vertical"),
        Index("ix_owner_notes_tenant", "tenant_code"),
    )

    tenant_code: Mapped[str] = mapped_column(String(64), nullable=False)
    vertical: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="", nullable=False)
