# Auto Marketplace Web CRM — durable PostgreSQL models (Sprint 1 Durable CRM).

from __future__ import annotations

from sqlalchemy import Float, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin


class AutoMarketplaceCrmCustomer(TimestampMixin, Base):
    __tablename__ = "auto_marketplace_crm_customers"
    __table_args__ = (
        Index("ix_am_crm_customers_tenant", "tenant_id"),
        Index("ix_am_crm_customers_tenant_email", "tenant_id", "email"),
        Index("ix_am_crm_customers_tenant_segment", "tenant_id", "segment"),
    )

    customer_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, server_default="default")
    first_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    last_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    email: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    phone: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    segment: Mapped[str] = mapped_column(String(64), nullable=False, default="standard")
    intent_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    lifetime_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    owner_agent_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    created_ts: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class AutoMarketplaceCrmLead(TimestampMixin, Base):
    __tablename__ = "auto_marketplace_crm_leads"
    __table_args__ = (
        Index("ix_am_crm_leads_tenant", "tenant_id"),
        Index("ix_am_crm_leads_tenant_dealer", "tenant_id", "dealer_id"),
        Index("ix_am_crm_leads_tenant_status", "tenant_id", "status"),
        Index("ix_am_crm_leads_tenant_customer", "tenant_id", "customer_id"),
    )

    lead_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, server_default="default")
    customer_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    vehicle_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    dealer_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="web")
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="new")
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    assigned_agent_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_ts: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    qualified_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class AutoMarketplaceCrmDeal(TimestampMixin, Base):
    __tablename__ = "auto_marketplace_crm_deals"
    __table_args__ = (
        Index("ix_am_crm_deals_tenant", "tenant_id"),
        Index("ix_am_crm_deals_tenant_dealer", "tenant_id", "dealer_id"),
        Index("ix_am_crm_deals_tenant_stage", "tenant_id", "stage"),
        Index("ix_am_crm_deals_tenant_customer", "tenant_id", "customer_id"),
    )

    deal_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, server_default="default")
    opportunity_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    customer_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    dealer_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    vehicle_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    stage: Mapped[str] = mapped_column(String(64), nullable=False, default="prospect")
    amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    probability: Mapped[float] = mapped_column(Float, nullable=False, default=0.1)
    win: Mapped[bool | None] = mapped_column(nullable=True)
    owner_agent_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    created_ts: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    closed_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
