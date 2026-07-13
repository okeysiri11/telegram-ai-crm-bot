# Analytics Automation Engine v1 — automated metric snapshots.

from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Date, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class SnapshotPeriod(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


SNAPSHOT_PERIODS = frozenset(p.value for p in SnapshotPeriod)


class AnalyticsSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "analytics_automation_engine_v1_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "metric_date",
            "period",
            name="uq_analytics_automation_engine_v1_snapshots_date_period",
        ),
        Index("ix_analytics_automation_engine_v1_snapshots_date", "metric_date"),
        Index("ix_analytics_automation_engine_v1_snapshots_period", "period"),
    )

    metric_date: Mapped[date] = mapped_column(Date, nullable=False)
    period: Mapped[str] = mapped_column(
        String(20),
        default=SnapshotPeriod.DAILY.value,
        nullable=False,
    )
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False)

    def __repr__(self) -> str:
        return f"<AnalyticsSnapshot date={self.metric_date} period={self.period}>"
