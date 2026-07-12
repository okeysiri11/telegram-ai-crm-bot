# Permission Engine — role permission grants.

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base

import database.models.permission  # noqa: F401
import database.models.role  # noqa: F401


class RolePermission(Base):
    __tablename__ = "permission_engine_role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_permission_engine_role_permissions"),
        Index("ix_permission_engine_role_permissions_role_id", "role_id"),
        Index("ix_permission_engine_role_permissions_permission_id", "permission_id"),
    )

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("permission_engine_roles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("permission_engine_permissions.id", ondelete="CASCADE"),
        primary_key=True,
    )

    def __repr__(self) -> str:
        return f"<RolePermission role_id={self.role_id} permission_id={self.permission_id}>"
