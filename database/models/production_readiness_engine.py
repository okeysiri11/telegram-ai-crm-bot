# Production Readiness Suite — health snapshots, metrics, and alerts.

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class HealthCheckStatus(str, enum.Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    SKIPPED = "skipped"


class AlertSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


HEALTH_CHECK_STATUSES = frozenset(s.value for s in HealthCheckStatus)
ALERT_SEVERITIES = frozenset(s.value for s in AlertSeverity)


class SystemHealth(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "system_health"
    __table_args__ = (
        Index("ix_system_health_check_name", "check_name"),
        Index("ix_system_health_status", "status"),
        Index("ix_system_health_checked_at", "checked_at"),
    )

    check_name: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    suite_version: Mapped[str] = mapped_column(String(32), default="v1", nullable=False)

    def __repr__(self) -> str:
        return f"<SystemHealth check={self.check_name} status={self.status}>"


class SystemMetric(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "system_metrics"
    __table_args__ = (
        Index("ix_system_metrics_name", "metric_name"),
        Index("ix_system_metrics_recorded_at", "recorded_at"),
    )

    metric_name: Mapped[str] = mapped_column(String(128), nullable=False)
    metric_value: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), default="count", nullable=False)
    tags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    def __repr__(self) -> str:
        return f"<SystemMetric name={self.metric_name} value={self.metric_value}>"


class SystemAlert(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "system_alerts"
    __table_args__ = (
        Index("ix_system_alerts_component", "component"),
        Index("ix_system_alerts_severity", "severity"),
        Index("ix_system_alerts_resolved_at", "resolved_at"),
    )

    alert_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    component: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<SystemAlert component={self.component} severity={self.severity}>"
