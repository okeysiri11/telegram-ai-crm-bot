# Permission Engine — role definitions.

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from database.models.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from database.models.user_role import UserRole


class EngineRoleCode(str, enum.Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    ACCOUNTANT = "ACCOUNTANT"
    LAWYER = "LAWYER"
    PARTNER = "PARTNER"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"


class Role(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "permission_engine_roles"
    __table_args__ = (
        UniqueConstraint("code", name="uq_permission_engine_roles_code"),
        Index("ix_permission_engine_roles_code", "code"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    user_links: Mapped[list["UserRole"]] = relationship(
        "database.models.user_role.UserRole",
        back_populates="role",
        cascade="all, delete-orphan",
        foreign_keys="database.models.user_role.UserRole.role_id",
    )

    def __repr__(self) -> str:
        return f"<Role id={self.id} code={self.code}>"
