# Platform metrics — request lifecycle, manager efficiency, daily aggregates.

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class RequestMetricStatus(str, enum.Enum):
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_CLIENT = "WAITING_CLIENT"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    CLOSED = "CLOSED"
    DEAL = "DEAL"


class RequestMetric(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Per-request lifecycle timings (source of truth for observability)."""

    __tablename__ = "request_metrics"
    __table_args__ = (
        UniqueConstraint("request_number", name="uq_request_metrics_number"),
        Index("ix_request_metrics_request_created_at", "request_created_at"),
        Index("ix_request_metrics_vertical", "vertical"),
        Index("ix_request_metrics_manager_id", "manager_id"),
        Index("ix_request_metrics_status", "status"),
        Index("ix_request_metrics_vertical_created", "vertical", "request_created_at"),
    )

    request_number: Mapped[str] = mapped_column(String(32), nullable=False)
    request_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    vertical: Mapped[str] = mapped_column(String(32), nullable=False)
    request_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default=RequestMetricStatus.NEW.value)
    manager_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    client_telegram_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    request_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    first_response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    time_to_assign_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_to_first_response_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_to_close_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    converted_to_deal: Mapped[bool] = mapped_column(default=False, nullable=False)


class ManagerMetric(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Daily manager efficiency rollups per vertical."""

    __tablename__ = "manager_metrics"
    __table_args__ = (
        UniqueConstraint(
            "manager_id",
            "metric_date",
            "vertical",
            name="uq_manager_metrics_manager_date_vertical",
        ),
        Index("ix_manager_metrics_manager_id", "manager_id"),
        Index("ix_manager_metrics_metric_date", "metric_date"),
        Index("ix_manager_metrics_vertical", "vertical"),
    )

    manager_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    metric_date: Mapped[date] = mapped_column(Date, nullable=False)
    vertical: Mapped[str] = mapped_column(String(32), nullable=False)

    requests_assigned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requests_with_response: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requests_closed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deals_won: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_response_time_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class PlatformMetricsDaily(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Daily platform-wide aggregates per vertical."""

    __tablename__ = "platform_metrics_daily"
    __table_args__ = (
        UniqueConstraint("metric_date", "vertical", name="uq_platform_metrics_daily_date_vertical"),
        Index("ix_platform_metrics_daily_metric_date", "metric_date"),
        Index("ix_platform_metrics_daily_vertical", "vertical"),
        Index("ix_platform_metrics_daily_created_at", "created_at"),
    )

    metric_date: Mapped[date] = mapped_column(Date, nullable=False)
    vertical: Mapped[str] = mapped_column(String(32), nullable=False)

    requests_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requests_assigned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requests_closed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    requests_deal: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_response_time_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    response_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    requests_by_type: Mapped[str | None] = mapped_column(Text, nullable=True)

    @property
    def average_response_time_seconds(self) -> float | None:
        if self.response_count <= 0:
            return None
        return self.total_response_time_seconds / self.response_count

    @property
    def conversion_to_deal_rate(self) -> float | None:
        if self.requests_created <= 0:
            return None
        return self.requests_deal / self.requests_created
