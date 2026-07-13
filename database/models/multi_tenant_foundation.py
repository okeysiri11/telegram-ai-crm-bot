# Multi-Tenant Foundation v1 — tenants registry, settings, and limits.

from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class TenantStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    ARCHIVED = "ARCHIVED"


class Tenant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Canonical tenant registry (mirrors partner_tenant rows by shared id)."""

    __tablename__ = "tenants"
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_tenants_company_code"),
        Index("ix_tenants_company_id", "company_id"),
        Index("ix_tenants_status", "status"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("multi_company_v1_companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=TenantStatus.ACTIVE.value,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Tenant code={self.code} company={self.company_id}>"


class TenantSettings(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenant_settings"
    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_tenant_settings_tenant_id"),
        Index("ix_tenant_settings_tenant_id", "tenant_id"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)
    locale: Mapped[str] = mapped_column(String(16), default="ru", nullable=False)
    branding: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    features: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    onboarding_completed: Mapped[bool] = mapped_column(default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<TenantSettings tenant={self.tenant_id}>"


class TenantLimits(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenant_limits"
    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_tenant_limits_tenant_id"),
        Index("ix_tenant_limits_tenant_id", "tenant_id"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    max_users: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    max_cars: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    max_leads: Mapped[int] = mapped_column(Integer, default=500, nullable=False)
    max_campaigns: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    max_documents: Mapped[int] = mapped_column(Integer, default=200, nullable=False)
    plan_code: Mapped[str | None] = mapped_column(String(30), nullable=True)

    def __repr__(self) -> str:
        return f"<TenantLimits tenant={self.tenant_id}>"
