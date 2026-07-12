# Observability Engine v1 — system, business, error, and performance metrics.

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class ErrorSeverity(str, enum.Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SystemMetric(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "observability_engine_v1_system_metrics"
    __table_args__ = (
        Index("ix_observability_v1_sys_name", "metric_name"),
        Index("ix_observability_v1_sys_recorded", "recorded_at"),
    )

    metric_name: Mapped[str] = mapped_column(String(128), nullable=False)
    metric_value: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), default="count", nullable=False)
    tags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<SystemMetric name={self.metric_name} value={self.metric_value}>"


class BusinessMetric(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "observability_engine_v1_business_metrics"
    __table_args__ = (
        Index("ix_observability_v1_biz_kpi", "kpi_name"),
        Index("ix_observability_v1_biz_recorded", "recorded_at"),
        Index("ix_observability_v1_biz_period", "period_start"),
    )

    kpi_name: Mapped[str] = mapped_column(String(128), nullable=False)
    kpi_value: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), default="count", nullable=False)
    dimensions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<BusinessMetric kpi={self.kpi_name} value={self.kpi_value}>"


class ErrorEvent(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "observability_engine_v1_error_events"
    __table_args__ = (
        Index("ix_observability_v1_err_source", "source"),
        Index("ix_observability_v1_err_severity", "severity"),
        Index("ix_observability_v1_err_recorded", "recorded_at"),
        Index("ix_observability_v1_err_resolved", "resolved"),
    )

    source: Mapped[str] = mapped_column(String(64), nullable=False)
    error_type: Mapped[str] = mapped_column(String(128), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    stack_trace: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    severity: Mapped[str] = mapped_column(
        String(20),
        default=ErrorSeverity.ERROR.value,
        nullable=False,
    )
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<ErrorEvent source={self.source} type={self.error_type}>"


class PerformanceMetric(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "observability_engine_v1_performance_metrics"
    __table_args__ = (
        Index("ix_observability_v1_perf_operation", "operation_name"),
        Index("ix_observability_v1_perf_recorded", "recorded_at"),
        Index("ix_observability_v1_perf_success", "success"),
    )

    operation_name: Mapped[str] = mapped_column(String(128), nullable=False)
    latency_ms: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<PerformanceMetric op={self.operation_name} "
            f"latency={self.latency_ms}ms>"
        )
