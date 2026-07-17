# KPI aggregate ORM models — manager and vertical rollups.

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ManagerDailyKpi(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "manager_daily_kpi"
    __table_args__ = (
        UniqueConstraint(
            "manager_id",
            "metric_date",
            "vertical",
            name="uq_manager_daily_kpi_manager_date_vertical",
        ),
        Index("ix_manager_daily_kpi_manager_id", "manager_id"),
        Index("ix_manager_daily_kpi_metric_date", "metric_date"),
        Index("ix_manager_daily_kpi_vertical", "vertical"),
    )

    manager_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    metric_date: Mapped[date] = mapped_column(Date, nullable=False)
    vertical: Mapped[str] = mapped_column(String(32), nullable=False, default="all")

    requests_assigned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requests_first_response: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requests_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requests_converted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requests_overdue: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    sla_compliant_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sla_total_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    total_first_response_seconds: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    total_response_seconds: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    total_resolution_seconds: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)


class ManagerMonthlyKpi(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "manager_monthly_kpi"
    __table_args__ = (
        UniqueConstraint(
            "manager_id",
            "metric_month",
            "vertical",
            name="uq_manager_monthly_kpi_manager_month_vertical",
        ),
        Index("ix_manager_monthly_kpi_manager_id", "manager_id"),
        Index("ix_manager_monthly_kpi_metric_month", "metric_month"),
        Index("ix_manager_monthly_kpi_vertical", "vertical"),
    )

    manager_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    metric_month: Mapped[date] = mapped_column(Date, nullable=False)
    vertical: Mapped[str] = mapped_column(String(32), nullable=False, default="all")

    requests_assigned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requests_first_response: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requests_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requests_converted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requests_overdue: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    sla_compliant_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sla_total_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    total_first_response_seconds: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    total_response_seconds: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    total_resolution_seconds: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)


class VerticalKpi(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "vertical_kpi"
    __table_args__ = (
        UniqueConstraint("vertical", "metric_date", name="uq_vertical_kpi_vertical_date"),
        Index("ix_vertical_kpi_vertical", "vertical"),
        Index("ix_vertical_kpi_metric_date", "metric_date"),
    )

    vertical: Mapped[str] = mapped_column(String(32), nullable=False)
    metric_date: Mapped[date] = mapped_column(Date, nullable=False)

    requests_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requests_assigned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requests_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requests_converted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requests_overdue: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    sla_compliant_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sla_total_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    total_first_response_seconds: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    response_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_resolution_seconds: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
