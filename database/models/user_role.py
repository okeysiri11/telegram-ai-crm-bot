# Permission Engine — user role assignments.

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.role import Role
    from database.models.users import User


class UserRole(Base):
    __tablename__ = "permission_engine_user_roles"
    __table_args__ = (
        Index("ix_permission_engine_user_roles_user_id", "user_id"),
        Index("ix_permission_engine_user_roles_role_id", "role_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("permission_engine_roles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(
        "User",
        back_populates="role_links",
        foreign_keys=[user_id],
    )
    role: Mapped[Role] = relationship(
        "Role",
        back_populates="user_links",
        foreign_keys=[role_id],
    )

    def __repr__(self) -> str:
        return f"<UserRole user_id={self.user_id} role_id={self.role_id}>"
