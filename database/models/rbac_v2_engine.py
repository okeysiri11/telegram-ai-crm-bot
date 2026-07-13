# RBAC v2 Engine — permissions, inheritance, role templates.

from __future__ import annotations

import enum
import uuid

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PermissionCategory(str, enum.Enum):
    MODULE = "module"
    ENTITY = "entity"
    TENANT = "tenant"
    BILLING = "billing"
    ANALYTICS = "analytics"


class RbacPermission(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "rbac_v2_permissions"
    __table_args__ = (
        UniqueConstraint("code", name="uq_rbac_v2_permissions_code"),
        Index("ix_rbac_v2_permissions_category", "category"),
        Index("ix_rbac_v2_permissions_parent", "parent_code"),
    )

    code: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    parent_code: Mapped[str | None] = mapped_column(
        String(128),
        ForeignKey("rbac_v2_permissions.code", ondelete="SET NULL"),
        nullable=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<RbacPermission code={self.code} category={self.category}>"


class RbacRoleGrant(Base):
    __tablename__ = "rbac_v2_role_grants"
    __table_args__ = (
        UniqueConstraint("role_code", "permission_code", name="uq_rbac_v2_role_grants"),
        Index("ix_rbac_v2_role_grants_role", "role_code"),
    )

    role_code: Mapped[str] = mapped_column(String(64), primary_key=True)
    permission_code: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("rbac_v2_permissions.code", ondelete="CASCADE"),
        primary_key=True,
    )


class RbacRoleInheritance(Base):
    __tablename__ = "rbac_v2_role_inheritance"
    __table_args__ = (
        UniqueConstraint("role_code", "parent_role_code", name="uq_rbac_v2_role_inheritance"),
        Index("ix_rbac_v2_role_inheritance_role", "role_code"),
    )

    role_code: Mapped[str] = mapped_column(String(64), primary_key=True)
    parent_role_code: Mapped[str] = mapped_column(String(64), primary_key=True)


class RbacRoleTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "rbac_v2_role_templates"
    __table_args__ = (
        UniqueConstraint("code", name="uq_rbac_v2_role_templates_code"),
        Index("ix_rbac_v2_role_templates_code", "code"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    role_codes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    permission_codes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    def __repr__(self) -> str:
        return f"<RbacRoleTemplate code={self.code}>"
