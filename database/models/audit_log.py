# Audit Log Engine model — immutable audit trail foundation.

from __future__ import annotations

import enum

from sqlalchemy import BigInteger, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class AuditAction(str, enum.Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    ASSIGN = "ASSIGN"
    STATUS_CHANGE = "STATUS_CHANGE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    EXPORT = "EXPORT"
    CREATE_PARTNER = "CREATE_PARTNER"
    UPDATE_PARTNER = "UPDATE_PARTNER"
    BLOCK_PARTNER = "BLOCK_PARTNER"
    CHANGE_LIMIT = "CHANGE_LIMIT"
    CHANGE_COMMISSION = "CHANGE_COMMISSION"
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    KYC_APPROVED = "KYC_APPROVED"
    KYC_REJECTED = "KYC_REJECTED"
    AML_FLAG_CREATED = "AML_FLAG_CREATED"
    PRICE_CHANGED = "PRICE_CHANGED"
    SPREAD_CHANGED = "SPREAD_CHANGED"
    MANAGER_MARGIN_CHANGED = "MANAGER_MARGIN_CHANGED"
    RISK_CHECK = "RISK_CHECK"
    RISK_OVERRIDE = "RISK_OVERRIDE"
    RISK_REJECTION = "RISK_REJECTION"
    QUOTE_UPDATED = "QUOTE_UPDATED"
    SOURCE_FAILED = "SOURCE_FAILED"


class AuditLog(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "audit_engine_logs"
    __table_args__ = (
        Index("ix_audit_engine_logs_user_id", "user_id"),
        Index("ix_audit_engine_logs_entity_type", "entity_type"),
        Index("ix_audit_engine_logs_entity_id", "entity_id"),
        Index("ix_audit_engine_logs_created_at", "created_at"),
    )

    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)

    action: Mapped[str] = mapped_column(String(50), nullable=False)

    old_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    ip_address: Mapped[str | None] = mapped_column(String(100), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} action={self.action} "
            f"entity={self.entity_type}:{self.entity_id}>"
        )
