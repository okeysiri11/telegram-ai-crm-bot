# User models — Sprint 34.2A unified identity (canonical platform account).

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from database.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin, VersionMixin

# Register FK targets on Base.metadata (avoids NoReferencedTableError on flush).
import database.models.multi_company  # noqa: F401
import database.models.multi_tenant_foundation  # noqa: F401
import database.models.user_identity_link  # noqa: F401

if TYPE_CHECKING:
    from database.models.user_identity_link import UserIdentityLink
    from database.models.user_role import PermissionUserRole


class User(UUIDPrimaryKeyMixin, CreatedAtMixin, VersionMixin, Base):
    """One platform account — Web, Telegram, Mobile, and API share this row."""

    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_telegram_id", "telegram_id", unique=True),
        Index("ix_users_is_active", "is_active"),
    )

    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Sprint 34.2A — unified identity fields (nullable for migration safety).
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", server_default="active", nullable=False)
    preferences: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Canonical CRM role (SUPER_ADMIN / AUTO_MANAGER / AGRO_MANAGER / CLIENT).
    # Permission-engine M2M roles remain the source of fine-grained grants.
    role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Subscribed verticals / workspaces, e.g. ["auto"] or ["agro", "crypto_otc"].
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
    identity_links: Mapped[list["UserIdentityLink"]] = relationship(
        "UserIdentityLink",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    @property
    def resolved_display_name(self) -> str | None:
        return self.display_name or self.full_name or self.username

    def __repr__(self) -> str:
        return f"<User id={self.id} telegram_id={self.telegram_id} email={self.email}>"
