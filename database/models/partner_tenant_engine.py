# Partner Tenant Engine v1 — multi-tenant isolation for partner portals.

from __future__ import annotations

import enum
import uuid

from sqlalchemy import BigInteger, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class TenantStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    ARCHIVED = "ARCHIVED"


class TenantRoleCode(str, enum.Enum):
    TENANT_ADMIN = "TENANT_ADMIN"
    TENANT_MANAGER = "TENANT_MANAGER"
    TENANT_VIEWER = "TENANT_VIEWER"


class TenantResourceType(str, enum.Enum):
    PARTNER = "partner"
    DEAL = "deal"
    CAR = "car"
    LEAD = "lead"
    CAMPAIGN = "campaign"
    CHANNEL = "channel"


class TenantBillingAccountType(str, enum.Enum):
    OPERATING = "OPERATING"
    SETTLEMENT = "SETTLEMENT"
    RESERVE = "RESERVE"


class PartnerTenant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "partner_tenant_engine_v1_tenants"
    __table_args__ = (
        UniqueConstraint("company_id", "code", name="uq_partner_tenant_engine_v1_tenants_company_code"),
        Index("ix_partner_tenant_engine_v1_tenants_company", "company_id"),
        Index("ix_partner_tenant_engine_v1_tenants_status", "status"),
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
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<PartnerTenant code={self.code} company={self.company_id}>"


class TenantUserRole(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "partner_tenant_engine_v1_user_roles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_partner_tenant_engine_v1_user_roles_tenant_user"),
        Index("ix_partner_tenant_engine_v1_user_roles_tenant", "tenant_id"),
        Index("ix_partner_tenant_engine_v1_user_roles_user", "user_id"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("multi_company_v1_companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    role_code: Mapped[str] = mapped_column(String(40), nullable=False)

    def __repr__(self) -> str:
        return f"<TenantUserRole tenant={self.tenant_id} user={self.user_id} role={self.role_code}>"


class TenantResourceBinding(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "partner_tenant_engine_v1_resource_bindings"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "resource_type",
            "resource_id",
            name="uq_partner_tenant_engine_v1_bindings_tenant_resource",
        ),
        Index("ix_partner_tenant_engine_v1_bindings_tenant", "tenant_id"),
        Index("ix_partner_tenant_engine_v1_bindings_company", "company_id"),
        Index("ix_partner_tenant_engine_v1_bindings_type", "resource_type"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("multi_company_v1_companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    resource_type: Mapped[str] = mapped_column(String(40), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<TenantResourceBinding tenant={self.tenant_id} "
            f"{self.resource_type}:{self.resource_id}>"
        )


class TenantBillingAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "partner_tenant_engine_v1_billing_accounts"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "account_type",
            "asset",
            name="uq_partner_tenant_engine_v1_billing_tenant_type_asset",
        ),
        Index("ix_partner_tenant_engine_v1_billing_tenant", "tenant_id"),
        Index("ix_partner_tenant_engine_v1_billing_company", "company_id"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("multi_company_v1_companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    treasury_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("treasury_engine_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    account_type: Mapped[str] = mapped_column(String(30), nullable=False)
    asset: Mapped[str] = mapped_column(String(20), nullable=False)
    treasury_code: Mapped[str] = mapped_column(String(64), nullable=False)
    billing_plan: Mapped[str | None] = mapped_column(String(50), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<TenantBillingAccount tenant={self.tenant_id} code={self.treasury_code}>"
