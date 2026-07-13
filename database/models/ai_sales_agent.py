# AI Sales Agent v1 — lead qualification, intent, recommendations, offers, follow-ups.

from __future__ import annotations

import enum
import uuid
from decimal import Decimal
from datetime import datetime

from sqlalchemy import (
    BigInteger,
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


class SalesLeadStatus(str, enum.Enum):
    NEW = "NEW"
    QUALIFIED = "QUALIFIED"
    NEGOTIATION = "NEGOTIATION"
    OFFER_SENT = "OFFER_SENT"
    WAITING_CUSTOMER = "WAITING_CUSTOMER"
    RESERVED = "RESERVED"
    SOLD = "SOLD"
    LOST = "LOST"


class SalesOfferStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class SalesLeadSource(str, enum.Enum):
    TELEGRAM = "TELEGRAM"
    INSTAGRAM = "INSTAGRAM"
    FACEBOOK = "FACEBOOK"
    WEBSITE = "WEBSITE"
    MARKETPLACE = "MARKETPLACE"
    PHONE = "PHONE"
    MANUAL = "MANUAL"


class SalesConversationDirection(str, enum.Enum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"


SALES_LEAD_STATUSES = frozenset(s.value for s in SalesLeadStatus)
SALES_OFFER_STATUSES = frozenset(s.value for s in SalesOfferStatus)
SALES_LEAD_SOURCES = frozenset(s.value for s in SalesLeadSource)
SALES_CONVERSATION_DIRECTIONS = frozenset(d.value for d in SalesConversationDirection)


class SalesLead(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_sales_agent_v1_sales_leads"
    __table_args__ = (
        CheckConstraint(
            "qualification_score >= 0 AND qualification_score <= 100",
            name="ck_ai_sales_agent_v1_lead_qualification_score",
        ),
        Index("ix_ai_sales_agent_v1_leads_tenant", "tenant_id"),
        Index("ix_ai_sales_agent_v1_leads_company", "company_id"),
        Index("ix_ai_sales_agent_v1_leads_status", "status"),
        Index("ix_ai_sales_agent_v1_leads_manager", "assigned_manager_id"),
        Index("ix_ai_sales_agent_v1_leads_automation", "automation_lead_id"),
        Index("ix_ai_sales_agent_v1_leads_marketplace", "marketplace_listing_id"),
        Index("ix_ai_sales_agent_v1_leads_follow_up", "next_follow_up_at"),
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
    automation_lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lead_automation_engine_v1_leads.id", ondelete="SET NULL"),
        nullable=True,
    )
    marketplace_listing_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lead_marketplace_engine_v1_listings.id", ondelete="SET NULL"),
        nullable=True,
    )
    recommended_car_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("car_engine_v1_cars.id", ondelete="SET NULL"),
        nullable=True,
    )
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    customer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str] = mapped_column(
        String(30),
        default=SalesLeadSource.MANUAL.value,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default=SalesLeadStatus.NEW.value,
        nullable=False,
    )
    intent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    qualification_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    budget_min: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    budget_max: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    assigned_manager_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_contact_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_follow_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    def __repr__(self) -> str:
        return f"<SalesLead tenant={self.tenant_id} status={self.status}>"


class SalesConversation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_sales_agent_v1_sales_conversations"
    __table_args__ = (
        Index("ix_ai_sales_agent_v1_conversations_lead", "sales_lead_id"),
        Index("ix_ai_sales_agent_v1_conversations_tenant", "tenant_id"),
    )

    sales_lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_sales_agent_v1_sales_leads.id", ondelete="CASCADE"),
        nullable=False,
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
    channel: Mapped[str] = mapped_column(String(30), nullable=False)
    direction: Mapped[str] = mapped_column(
        String(20),
        default=SalesConversationDirection.INBOUND.value,
        nullable=False,
    )
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    intent_detected: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    def __repr__(self) -> str:
        return f"<SalesConversation lead={self.sales_lead_id} direction={self.direction}>"


class SalesOffer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_sales_agent_v1_sales_offers"
    __table_args__ = (
        CheckConstraint("offer_price >= 0", name="ck_ai_sales_agent_v1_offer_price"),
        CheckConstraint("discount_amount >= 0", name="ck_ai_sales_agent_v1_offer_discount"),
        Index("ix_ai_sales_agent_v1_offers_lead", "sales_lead_id"),
        Index("ix_ai_sales_agent_v1_offers_tenant", "tenant_id"),
        Index("ix_ai_sales_agent_v1_offers_car", "car_id"),
        Index("ix_ai_sales_agent_v1_offers_status", "status"),
        Index("ix_ai_sales_agent_v1_offers_document", "document_id"),
    )

    sales_lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_sales_agent_v1_sales_leads.id", ondelete="CASCADE"),
        nullable=False,
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
    car_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("car_engine_v1_cars.id", ondelete="RESTRICT"),
        nullable=False,
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_engine_v1_documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    offer_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=SalesOfferStatus.DRAFT.value,
        nullable=False,
    )
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    terms: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    def __repr__(self) -> str:
        return f"<SalesOffer lead={self.sales_lead_id} status={self.status}>"


class CustomerPreference(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_sales_agent_v1_customer_preferences"
    __table_args__ = (
        UniqueConstraint("sales_lead_id", name="uq_ai_sales_agent_v1_prefs_lead"),
        CheckConstraint("min_year IS NULL OR max_year IS NULL OR min_year <= max_year", name="ck_ai_sales_agent_v1_prefs_year"),
        Index("ix_ai_sales_agent_v1_prefs_tenant", "tenant_id"),
    )

    sales_lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_sales_agent_v1_sales_leads.id", ondelete="CASCADE"),
        nullable=False,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    preferred_makes: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    preferred_models: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    body_types: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    min_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_mileage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    budget_min: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    budget_max: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    fuel_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    transmission: Mapped[str | None] = mapped_column(String(30), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<CustomerPreference lead={self.sales_lead_id}>"
