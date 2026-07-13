# Automotive Partner Integration v1 — partner registry, products, dealer sources, insurance offers.

from __future__ import annotations

import enum
import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin


class AutomotivePartnerType(str, enum.Enum):
    INSURANCE = "INSURANCE"
    DEALER = "DEALER"
    LEASING = "LEASING"
    DELIVERY = "DELIVERY"
    LEGAL = "LEGAL"


class DealerSourceType(str, enum.Enum):
    TELEGRAM_CHANNEL = "telegram_channel"
    API = "api"
    MANUAL = "manual"


class AutomotiveRegistryPartner(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Automotive partner registry (logical: partners)."""

    __tablename__ = "automotive_partner_v1_partners"
    __table_args__ = (
        UniqueConstraint("code", name="uq_automotive_partner_v1_partners_code"),
        Index("ix_automotive_partner_v1_partners_type", "partner_type"),
        Index("ix_automotive_partner_v1_partners_active", "is_active"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    partner_type: Mapped[str] = mapped_column(String(32), nullable=False)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    telegram_channel: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tenant_mode_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<AutomotiveRegistryPartner code={self.code} type={self.partner_type}>"


class AutomotivePartnerProduct(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Partner product catalog (logical: partner_products)."""

    __tablename__ = "automotive_partner_v1_partner_products"
    __table_args__ = (
        UniqueConstraint("partner_id", "product_code", name="uq_automotive_partner_v1_products_code"),
        Index("ix_automotive_partner_v1_products_partner", "partner_id"),
        Index("ix_automotive_partner_v1_products_active", "is_active"),
    )

    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_partner_v1_partners.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    sort_order: Mapped[int] = mapped_column(default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<AutomotivePartnerProduct code={self.product_code} partner={self.partner_id}>"


class AutomotiveDealerSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Dealer inventory/pricing source (logical: dealer_sources)."""

    __tablename__ = "automotive_partner_v1_dealer_sources"
    __table_args__ = (
        UniqueConstraint("partner_id", "source_code", name="uq_automotive_partner_v1_dealer_sources_code"),
        Index("ix_automotive_partner_v1_dealer_sources_tenant", "tenant_id"),
        Index("ix_automotive_partner_v1_dealer_sources_partner", "partner_id"),
        Index("ix_automotive_partner_v1_dealer_sources_active", "is_active"),
    )

    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_partner_v1_partners.id", ondelete="CASCADE"),
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="CASCADE"),
        nullable=True,
    )
    source_code: Mapped[str] = mapped_column(String(64), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    channel_username: Mapped[str | None] = mapped_column(String(128), nullable=True)
    channel_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<AutomotiveDealerSource code={self.source_code} type={self.source_type}>"


class AutomotiveInsuranceOffer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Insurance offer linked to partner product (logical: insurance_offers)."""

    __tablename__ = "automotive_partner_v1_insurance_offers"
    __table_args__ = (
        Index("ix_automotive_partner_v1_insurance_offers_partner", "partner_id"),
        Index("ix_automotive_partner_v1_insurance_offers_product", "product_id"),
        Index("ix_automotive_partner_v1_insurance_offers_tenant", "tenant_id"),
        Index("ix_automotive_partner_v1_insurance_offers_active", "is_active"),
    )

    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_partner_v1_partners.id", ondelete="CASCADE"),
        nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_partner_v1_partner_products.id", ondelete="CASCADE"),
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="CASCADE"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    premium_from: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(8), default="UAH", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<AutomotiveInsuranceOffer title={self.title} product={self.product_id}>"
