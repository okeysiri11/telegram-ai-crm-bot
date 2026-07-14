# Role models — RBAC v2.

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from database.models.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from database.models.permissions import RolePermission
    from database.models.users import User


class Role(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("code", name="uq_roles_code"),
        Index("ix_roles_code", "code"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    user_links: Mapped[list["UserRole"]] = relationship(
        back_populates="role",
        cascade="all, delete-orphan",
    )
    permission_links: Mapped[list[RolePermission]] = relationship(
        back_populates="role",
        cascade="all, delete-orphan",
    )


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        Index("ix_user_roles_user_id", "user_id"),
        Index("ix_user_roles_role_id", "role_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    user: Mapped[User] = relationship(
        foreign_keys=[user_id],
    )
    role: Mapped[Role] = relationship(
        back_populates="user_links",
        foreign_keys=[role_id],
    )
    assigner: Mapped[User | None] = relationship(
        foreign_keys=[assigned_by],
    )
