# Trust Security Engine v1 — access logs, audits, approvals, emergency revoke.

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin


class AccessAction(str, enum.Enum):
    READ = "READ"
    WRITE = "WRITE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    VIEW = "VIEW"
    EXPORT = "EXPORT"


ACCESS_ACTIONS = frozenset(a.value for a in AccessAction)


class PermissionAuditAction(str, enum.Enum):
    GRANT = "GRANT"
    REVOKE = "REVOKE"
    CHANGE = "CHANGE"


PERMISSION_AUDIT_ACTIONS = frozenset(a.value for a in PermissionAuditAction)


class ExportFormat(str, enum.Enum):
    CSV = "CSV"
    JSON = "JSON"
    PDF = "PDF"
    XLSX = "XLSX"


EXPORT_FORMATS = frozenset(f.value for f in ExportFormat)


class ApiAccessResult(str, enum.Enum):
    SUCCESS = "SUCCESS"
    DENIED = "DENIED"
    RATE_LIMITED = "RATE_LIMITED"
    ERROR = "ERROR"


API_ACCESS_RESULTS = frozenset(r.value for r in ApiAccessResult)


class ContentApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


CONTENT_APPROVAL_STATUSES = frozenset(s.value for s in ContentApprovalStatus)


class RevokeScope(str, enum.Enum):
    USER_GLOBAL = "USER_GLOBAL"
    TENANT_USER = "TENANT_USER"
    API_CLIENT = "API_CLIENT"
    API_KEY = "API_KEY"


REVOKE_SCOPES = frozenset(s.value for s in RevokeScope)


class RevokeStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"


class SecurityAccessLog(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "trust_security_engine_v1_access_logs"
    __table_args__ = (
        Index("ix_trust_security_engine_v1_access_user", "user_id"),
        Index("ix_trust_security_engine_v1_access_tenant", "tenant_id"),
        Index("ix_trust_security_engine_v1_access_company", "company_id"),
        Index("ix_trust_security_engine_v1_access_resource", "resource_type"),
        Index("ix_trust_security_engine_v1_access_created", "created_at"),
    )

    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(100), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


class SecurityPermissionAudit(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "trust_security_engine_v1_permission_audits"
    __table_args__ = (
        Index("ix_trust_security_engine_v1_perm_actor", "actor_id"),
        Index("ix_trust_security_engine_v1_perm_subject", "subject_user_id"),
        Index("ix_trust_security_engine_v1_perm_tenant", "tenant_id"),
        Index("ix_trust_security_engine_v1_perm_action", "audit_action"),
    )

    actor_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    subject_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    permission_code: Mapped[str] = mapped_column(String(80), nullable=False)
    audit_action: Mapped[str] = mapped_column(String(30), nullable=False)
    old_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class SecurityExportLog(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "trust_security_engine_v1_export_logs"
    __table_args__ = (
        Index("ix_trust_security_engine_v1_export_user", "user_id"),
        Index("ix_trust_security_engine_v1_export_tenant", "tenant_id"),
        Index("ix_trust_security_engine_v1_export_resource", "resource_type"),
    )

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    export_format: Mapped[str] = mapped_column(String(20), nullable=False)
    record_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


class SecurityApiAccessLog(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "trust_security_engine_v1_api_access_logs"
    __table_args__ = (
        Index("ix_trust_security_engine_v1_api_client", "api_client_id"),
        Index("ix_trust_security_engine_v1_api_key", "api_key_id"),
        Index("ix_trust_security_engine_v1_api_tenant", "tenant_id"),
        Index("ix_trust_security_engine_v1_api_path", "path"),
        Index("ix_trust_security_engine_v1_api_created", "created_at"),
    )

    api_client_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    api_key_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    path: Mapped[str] = mapped_column(String(255), nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result: Mapped[str] = mapped_column(String(30), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(100), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


class SecurityContentApproval(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trust_security_engine_v1_content_approvals"
    __table_args__ = (
        Index("ix_trust_security_engine_v1_content_tenant", "tenant_id"),
        Index("ix_trust_security_engine_v1_content_status", "status"),
        Index("ix_trust_security_engine_v1_content_submitter", "submitted_by"),
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content_ref: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body_preview: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30),
        default=ContentApprovalStatus.PENDING.value,
        nullable=False,
    )
    submitted_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reviewed_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)


class SecurityEmergencyRevoke(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trust_security_engine_v1_emergency_revokes"
    __table_args__ = (
        Index("ix_trust_security_engine_v1_revoke_scope", "scope"),
        Index("ix_trust_security_engine_v1_revoke_target", "target_ref"),
        Index("ix_trust_security_engine_v1_revoke_status", "status"),
        Index("ix_trust_security_engine_v1_revoke_tenant", "tenant_id"),
    )

    scope: Mapped[str] = mapped_column(String(30), nullable=False)
    target_ref: Mapped[str] = mapped_column(String(120), nullable=False)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    revoked_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=RevokeStatus.ACTIVE.value,
        nullable=False,
    )
    released_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actions_taken: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
