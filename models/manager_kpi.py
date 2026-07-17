# KPI domain schemas — API payloads and period helpers.

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal

KpiPeriod = Literal["day", "week", "month", "all_time"]


def period_bounds(period: KpiPeriod, *, anchor: date | None = None) -> tuple[date | None, date]:
    """Return (start_date inclusive, end_date inclusive) for a KPI period."""
    end = anchor or datetime.now(timezone.utc).date()
    if period == "day":
        return end, end
    if period == "week":
        return end - timedelta(days=6), end
    if period == "month":
        return end.replace(day=1), end
    return None, end


def month_start(value: date) -> date:
    return value.replace(day=1)


@dataclass
class KpiTotals:
    requests_assigned: int = 0
    requests_first_response: int = 0
    requests_completed: int = 0
    requests_converted: int = 0
    requests_created: int = 0
    requests_overdue: int = 0
    sla_compliant_count: int = 0
    sla_total_count: int = 0
    total_first_response_seconds: int = 0
    total_response_seconds: int = 0
    total_resolution_seconds: int = 0
    response_count: int = 0

    @property
    def first_response_time_seconds(self) -> float | None:
        if self.requests_first_response <= 0:
            return None
        return self.total_first_response_seconds / self.requests_first_response

    @property
    def average_response_time_seconds(self) -> float | None:
        count = self.response_count or self.requests_first_response
        if count <= 0:
            return None
        total = self.total_response_seconds or self.total_first_response_seconds
        return total / count

    @property
    def resolution_time_seconds(self) -> float | None:
        if self.requests_completed <= 0:
            return None
        return self.total_resolution_seconds / self.requests_completed

    @property
    def sla_compliance_percent(self) -> float | None:
        if self.sla_total_count <= 0:
            return None
        return round(100.0 * self.sla_compliant_count / self.sla_total_count, 2)

    @property
    def conversion_rate(self) -> float | None:
        base = self.requests_completed or self.requests_assigned
        if base <= 0:
            return None
        return round(self.requests_converted / base, 4)

    @property
    def requests_per_manager(self) -> int:
        return self.requests_assigned

    @property
    def requests_per_vertical(self) -> int:
        return self.requests_created or self.requests_assigned

    def to_metrics_dict(self) -> dict[str, Any]:
        return {
            "first_response_time_seconds": self.first_response_time_seconds,
            "average_response_time_seconds": self.average_response_time_seconds,
            "resolution_time_seconds": self.resolution_time_seconds,
            "sla_compliance_percent": self.sla_compliance_percent,
            "requests_per_manager": self.requests_per_manager,
            "conversion_rate": self.conversion_rate,
            "requests_per_vertical": self.requests_per_vertical,
            "overdue_requests_count": self.requests_overdue,
            "requests_assigned": self.requests_assigned,
            "requests_completed": self.requests_completed,
            "requests_converted": self.requests_converted,
        }


@dataclass
class ManagerKpiSnapshot:
    manager_id: str
    period: KpiPeriod
    totals: KpiTotals = field(default_factory=KpiTotals)
    by_vertical: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "manager_id": self.manager_id,
            "period": self.period,
            **self.totals.to_metrics_dict(),
            "by_vertical": self.by_vertical,
        }


@dataclass
class VerticalKpiSnapshot:
    vertical: str
    period: KpiPeriod
    totals: KpiTotals = field(default_factory=KpiTotals)

    def to_dict(self) -> dict[str, Any]:
        return {
            "vertical": self.vertical.upper(),
            "period": self.period,
            **self.totals.to_metrics_dict(),
        }


@dataclass
class PlatformKpiSnapshot:
    period: KpiPeriod
    totals: KpiTotals = field(default_factory=KpiTotals)
    by_vertical: dict[str, dict[str, Any]] = field(default_factory=dict)
    manager_rankings: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "period": self.period,
            **self.totals.to_metrics_dict(),
            "by_vertical": self.by_vertical,
            "manager_rankings": self.manager_rankings,
        }
