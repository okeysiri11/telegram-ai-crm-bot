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



class AutoMarketplaceCrmTask(TimestampMixin, Base):
    __tablename__ = "auto_marketplace_crm_tasks"
    __table_args__ = (
        Index("ix_am_crm_tasks_tenant", "tenant_id"),
        Index("ix_am_crm_tasks_tenant_status", "tenant_id", "status"),
        Index("ix_am_crm_tasks_tenant_assignee", "tenant_id", "assigned_agent_id"),
        Index("ix_am_crm_tasks_tenant_customer", "tenant_id", "customer_id"),
        Index("ix_am_crm_tasks_tenant_lead", "tenant_id", "lead_id"),
        Index("ix_am_crm_tasks_tenant_deal", "tenant_id", "deal_id"),
    )

    task_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, server_default="default")
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(64), nullable=False, default="pending")
    priority: Mapped[str] = mapped_column(String(64), nullable=False, default="normal")
    customer_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    lead_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    deal_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    assigned_agent_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    created_by: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    due_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    completed_at: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_ts: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class AutoMarketplaceCrmActivity(TimestampMixin, Base):
    __tablename__ = "auto_marketplace_crm_activities"
    __table_args__ = (
        Index("ix_am_crm_activities_tenant", "tenant_id"),
        Index("ix_am_crm_activities_tenant_type", "tenant_id", "activity_type"),
        Index("ix_am_crm_activities_tenant_customer", "tenant_id", "customer_id"),
        Index("ix_am_crm_activities_tenant_lead", "tenant_id", "lead_id"),
        Index("ix_am_crm_activities_tenant_deal", "tenant_id", "deal_id"),
        Index("ix_am_crm_activities_tenant_task", "tenant_id", "task_id"),
        Index("ix_am_crm_activities_tenant_idempotency", "tenant_id", "idempotency_key"),
    )

    activity_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(128), nullable=False, server_default="default")
    activity_type: Mapped[str] = mapped_column(String(64), nullable=False, default="note")
    customer_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    lead_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    deal_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    task_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    agent_id: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    subject: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    created_ts: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
