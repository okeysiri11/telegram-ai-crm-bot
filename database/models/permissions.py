# Hierarchical RBAC permission models.

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from database.models.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from database.models.roles import Role


class RbacPermission(Base):
    __tablename__ = "rbac_permissions"
    __table_args__ = (
        Index("ix_rbac_permissions_level", "level"),
        Index("ix_rbac_permissions_module", "module"),
    )

    code: Mapped[str] = mapped_column(String(128), primary_key=True)
    level: Mapped[str] = mapped_column(String(32), nullable=False)
    module: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entity: Mapped[str | None] = mapped_column(String(64), nullable=True)
    parent_code: Mapped[str | None] = mapped_column(
        String(128),
        ForeignKey("rbac_permissions.code", ondelete="SET NULL"),
        nullable=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    parent: Mapped[RbacPermission | None] = relationship(
        remote_side=[code],
        back_populates="children",
    )
    children: Mapped[list[RbacPermission]] = relationship(back_populates="parent")
    role_grants: Mapped[list[RbacRoleGrant]] = relationship(
        back_populates="permission",
        cascade="all, delete-orphan",
    )


class RbacRoleGrant(Base):
    __tablename__ = "rbac_role_grants"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_code", name="uq_rbac_role_grants"),
        Index("ix_rbac_role_grants_role_id", "role_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    permission_code: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("rbac_permissions.code", ondelete="CASCADE"),
        nullable=False,
    )

    role: Mapped[Role] = relationship(back_populates="rbac_grants")
    permission: Mapped[RbacPermission] = relationship(back_populates="role_grants")
