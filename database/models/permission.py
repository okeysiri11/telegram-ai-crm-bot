# Permission Engine — permission definitions.

from __future__ import annotations

import enum

from sqlalchemy import Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import UUIDPrimaryKeyMixin


class EnginePermissionCode(str, enum.Enum):
    VIEW_DEALS = "VIEW_DEALS"
    CREATE_DEALS = "CREATE_DEALS"
    EDIT_DEALS = "EDIT_DEALS"
    DELETE_DEALS = "DELETE_DEALS"
    VIEW_LEDGER = "VIEW_LEDGER"
    EDIT_LEDGER = "EDIT_LEDGER"
    VIEW_COMMISSIONS = "VIEW_COMMISSIONS"
    PAY_COMMISSIONS = "PAY_COMMISSIONS"
    VIEW_USERS = "VIEW_USERS"
    CREATE_USERS = "CREATE_USERS"
    EDIT_USERS = "EDIT_USERS"
    DELETE_USERS = "DELETE_USERS"
    VIEW_AUDIT = "VIEW_AUDIT"
    EXPORT_AUDIT = "EXPORT_AUDIT"
    VIEW_REPORTS = "VIEW_REPORTS"
    EXPORT_REPORTS = "EXPORT_REPORTS"
    MANAGE_SETTINGS = "MANAGE_SETTINGS"


class Permission(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "permission_engine_permissions"
    __table_args__ = (
        UniqueConstraint("code", name="uq_permission_engine_permissions_code"),
        Index("ix_permission_engine_permissions_code", "code"),
    )

    code: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Permission id={self.id} code={self.code}>"
