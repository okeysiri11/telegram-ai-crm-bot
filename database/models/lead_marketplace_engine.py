# Lead Marketplace Engine v1 — distribution, auction, exclusive leads, pricing, quality scoring.

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class MarketplaceDistributionMode(str, enum.Enum):
    DISTRIBUTION = "DISTRIBUTION"
    AUCTION = "AUCTION"
    EXCLUSIVE = "EXCLUSIVE"


class MarketplaceListingStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    CLOSED = "CLOSED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class MarketplaceOfferType(str, enum.Enum):
    BID = "BID"
    DISTRIBUTION_ACCEPT = "DISTRIBUTION_ACCEPT"
    EXCLUSIVE_PURCHASE = "EXCLUSIVE_PURCHASE"


class MarketplaceOfferStatus(str, enum.Enum):
    PENDING = "PENDING"
    WINNING = "WINNING"
    ACCEPTED = "ACCEPTED"
    OUTBID = "OUTBID"
    DECLINED = "DECLINED"
    WITHDRAWN = "WITHDRAWN"
    REJECTED = "REJECTED"


MARKETPLACE_DISTRIBUTION_MODES = frozenset(m.value for m in MarketplaceDistributionMode)
MARKETPLACE_LISTING_STATUSES = frozenset(s.value for s in MarketplaceListingStatus)
MARKETPLACE_OFFER_TYPES = frozenset(t.value for t in MarketplaceOfferType)
MARKETPLACE_OFFER_STATUSES = frozenset(s.value for s in MarketplaceOfferStatus)


class LeadMarketplaceListing(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "lead_marketplace_engine_v1_listings"
    __table_args__ = (
        CheckConstraint("quality_score >= 0 AND quality_score <= 100", name="ck_lead_marketplace_v1_listing_score"),
        CheckConstraint("base_price >= 0", name="ck_lead_marketplace_v1_listing_base_price"),
        Index("ix_lead_marketplace_v1_listings_tenant", "tenant_id"),
        Index("ix_lead_marketplace_v1_listings_company", "company_id"),
        Index("ix_lead_marketplace_v1_listings_lead", "automation_lead_id"),
        Index("ix_lead_marketplace_v1_listings_mode", "distribution_mode"),
        Index("ix_lead_marketplace_v1_listings_status", "status"),
        Index("ix_lead_marketplace_v1_listings_score", "quality_score"),
        Index("ix_lead_marketplace_v1_listings_expires", "expires_at"),
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
    automation_lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lead_automation_engine_v1_leads.id", ondelete="CASCADE"),
        nullable=False,
    )
    distribution_mode: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=MarketplaceListingStatus.DRAFT.value,
        nullable=False,
    )
    base_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    reserve_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    final_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    quality_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quality_factors: Mapped[dict] = mapped_column(JSONB, nullable=False)
    pricing_breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False)
    buyer_tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="SET NULL"),
        nullable=True,
    )
    exclusive_buyer_tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="SET NULL"),
        nullable=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<LeadMarketplaceListing lead={self.automation_lead_id} "
            f"mode={self.distribution_mode} status={self.status}>"
        )


class LeadMarketplaceOffer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "lead_marketplace_engine_v1_offers"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_lead_marketplace_v1_offer_amount"),
        Index("ix_lead_marketplace_v1_offers_listing", "listing_id"),
        Index("ix_lead_marketplace_v1_offers_buyer", "buyer_tenant_id"),
        Index("ix_lead_marketplace_v1_offers_type", "offer_type"),
        Index("ix_lead_marketplace_v1_offers_status", "status"),
        Index("ix_lead_marketplace_v1_offers_amount", "amount"),
    )

    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lead_marketplace_engine_v1_listings.id", ondelete="CASCADE"),
        nullable=False,
    )
    buyer_tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    actor_id: Mapped[int] = mapped_column(Integer, nullable=False)
    offer_type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=MarketplaceOfferStatus.PENDING.value,
        nullable=False,
    )
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<LeadMarketplaceOffer listing={self.listing_id} amount={self.amount} status={self.status}>"


class LeadMarketplacePricingRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "lead_marketplace_engine_v1_pricing_rules"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_lead_marketplace_v1_pricing_tenant_code"),
        CheckConstraint("base_price >= 0", name="ck_lead_marketplace_v1_pricing_base"),
        CheckConstraint(
            "min_quality_score >= 0 AND max_quality_score <= 100",
            name="ck_lead_marketplace_v1_pricing_score_range",
        ),
        Index("ix_lead_marketplace_v1_pricing_tenant", "tenant_id"),
        Index("ix_lead_marketplace_v1_pricing_active", "is_active"),
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
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    min_quality_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_quality_score: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    base_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    price_per_score_point: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        default=Decimal("0"),
        nullable=False,
    )
    auction_premium_percent: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        default=Decimal("0"),
        nullable=False,
    )
    exclusive_multiplier: Mapped[Decimal] = mapped_column(
        Numeric(8, 2),
        default=Decimal("1.5"),
        nullable=False,
    )
    default_distribution_mode: Mapped[str] = mapped_column(
        String(30),
        default=MarketplaceDistributionMode.DISTRIBUTION.value,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<LeadMarketplacePricingRule tenant={self.tenant_id} code={self.code}>"
