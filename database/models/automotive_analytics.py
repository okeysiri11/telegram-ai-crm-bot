# Automotive Analytics Engine v1 — inventory, sales, profitability metrics.

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

import database.models.automotive_inventory  # noqa: F401


class AgingBucket(str, enum.Enum):
    DAYS_0_30 = "DAYS_0_30"
    DAYS_31_60 = "DAYS_31_60"
    DAYS_61_90 = "DAYS_61_90"
    DAYS_90_PLUS = "DAYS_90_PLUS"


class InventoryMetrics(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_analytics_v1_inventory_metrics"
    __table_args__ = (
        Index("ix_automotive_analytics_v1_im_vehicle_id", "vehicle_id"),
        Index("ix_automotive_analytics_v1_im_metric_date", "metric_date"),
        Index("ix_automotive_analytics_v1_im_aging_bucket", "aging_bucket"),
        Index("ix_automotive_analytics_v1_im_tenant", "tenant_id"),
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
    )

    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_v1_vehicles.id", ondelete="CASCADE"),
        nullable=True,
    )
    metric_date: Mapped[date] = mapped_column(Date, nullable=False)
    days_in_inventory: Mapped[int | None] = mapped_column(Integer, nullable=True)
    aging_bucket: Mapped[str | None] = mapped_column(String(20), nullable=True)
    vehicle_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    inventory_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    in_stock_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sold_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    turnover_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<InventoryMetrics id={self.id} vehicle={self.vehicle_id} "
            f"date={self.metric_date}>"
        )


class SalesMetrics(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_analytics_v1_sales_metrics"
    __table_args__ = (
        Index("ix_automotive_analytics_v1_sm_metric_date", "metric_date"),
        Index("ix_automotive_analytics_v1_sm_tenant", "tenant_id"),
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
    )

    metric_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_leads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_leads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    contacted_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    test_drive_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    negotiation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    contract_signed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    paid_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    delivered_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    conversion_rate: Mapped[Decimal] = mapped_column(
        Numeric(8, 4),
        default=Decimal("0"),
        nullable=False,
    )
    total_pipeline_budget: Mapped[Decimal | None] = mapped_column(
        Numeric(20, 2),
        nullable=True,
    )
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)

    def __repr__(self) -> str:
        return f"<SalesMetrics id={self.id} date={self.metric_date}>"


class ProfitabilityMetrics(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "automotive_analytics_v1_profitability_metrics"
    __table_args__ = (
        Index("ix_automotive_analytics_v1_pm_vehicle_id", "vehicle_id"),
        Index("ix_automotive_analytics_v1_pm_metric_date", "metric_date"),
        CheckConstraint("margin_percent >= -100", name="ck_automotive_analytics_v1_pm_margin"),
        Index("ix_automotive_analytics_v1_pm_tenant", "tenant_id"),
    )

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=True,
    )

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automotive_v1_vehicles.id", ondelete="CASCADE"),
        nullable=False,
    )
    metric_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    sale_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    target_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    margin_amount: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    margin_percent: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    roi_percent: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)

    def __repr__(self) -> str:
        return (
            f"<ProfitabilityMetrics vehicle={self.vehicle_id} "
            f"roi={self.roi_percent}>"
        )
