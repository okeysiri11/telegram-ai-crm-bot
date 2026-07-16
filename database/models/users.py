# User models — RBAC v2.

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from database.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from database.models.user_role import PermissionUserRole


class User(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_telegram_id", "telegram_id", unique=True),
        Index("ix_users_is_active", "is_active"),
    )

    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Canonical CRM role (SUPER_ADMIN / AUTO_MANAGER / AGRO_MANAGER / CLIENT).
    # Permission-engine M2M roles remain the source of fine-grained grants.
    role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Subscribed verticals for managers, e.g. ["auto"] or ["agro", "auto"].
    verticals: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
    )

    role_links: Mapped[list["PermissionUserRole"]] = relationship(
        "PermissionUserRole",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} telegram_id={self.telegram_id}>"
