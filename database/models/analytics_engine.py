# Analytics Engine v1 — lead, sales, advertising, and manager statistics.

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class LeadStatistics(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "analytics_engine_v1_lead_statistics"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "metric_date",
            name="uq_analytics_engine_v1_lead_stats_tenant_date",
        ),
        Index("ix_analytics_engine_v1_lead_stats_tenant", "tenant_id"),
        Index("ix_analytics_engine_v1_lead_stats_date", "metric_date"),
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
    metric_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_leads: Mapped[int] = mapped_column(default=0, nullable=False)
    qualified_leads: Mapped[int] = mapped_column(default=0, nullable=False)
    leads_by_source: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    cpl: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    conversion_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    lead_source_roi: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<LeadStatistics tenant={self.tenant_id} date={self.metric_date}>"


class SalesStatistics(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "analytics_engine_v1_sales_statistics"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "metric_date",
            name="uq_analytics_engine_v1_sales_stats_tenant_date",
        ),
        Index("ix_analytics_engine_v1_sales_stats_tenant", "tenant_id"),
        Index("ix_analytics_engine_v1_sales_stats_date", "metric_date"),
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
    metric_date: Mapped[date] = mapped_column(Date, nullable=False)
    deals_won: Mapped[int] = mapped_column(default=0, nullable=False)
    deals_lost: Mapped[int] = mapped_column(default=0, nullable=False)
    total_revenue: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    average_deal_size: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    conversion_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    vehicle_turnover: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<SalesStatistics tenant={self.tenant_id} date={self.metric_date}>"


class AdvertisingStatistics(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "analytics_engine_v1_advertising_statistics"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "metric_date",
            name="uq_analytics_engine_v1_ad_stats_tenant_date",
        ),
        Index("ix_analytics_engine_v1_ad_stats_tenant", "tenant_id"),
        Index("ix_analytics_engine_v1_ad_stats_date", "metric_date"),
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
    metric_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_spend: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    total_impressions: Mapped[int] = mapped_column(default=0, nullable=False)
    total_clicks: Mapped[int] = mapped_column(default=0, nullable=False)
    leads_from_ads: Mapped[int] = mapped_column(default=0, nullable=False)
    cac: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    cpl: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    campaign_metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<AdvertisingStatistics tenant={self.tenant_id} date={self.metric_date}>"


class ManagerStatistics(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "analytics_engine_v1_manager_statistics"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "manager_id",
            "metric_date",
            name="uq_analytics_engine_v1_mgr_stats_tenant_mgr_date",
        ),
        Index("ix_analytics_engine_v1_mgr_stats_tenant", "tenant_id"),
        Index("ix_analytics_engine_v1_mgr_stats_manager", "manager_id"),
        Index("ix_analytics_engine_v1_mgr_stats_date", "metric_date"),
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
    manager_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    metric_date: Mapped[date] = mapped_column(Date, nullable=False)
    leads_assigned: Mapped[int] = mapped_column(default=0, nullable=False)
    deals_closed: Mapped[int] = mapped_column(default=0, nullable=False)
    revenue: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    conversion_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    performance_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<ManagerStatistics manager={self.manager_id} date={self.metric_date}>"
