# Analytics KPI scaffold — models + calculators (no DB writes yet).

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LeadMetrics:
    total_leads: int = 0
    new_today: int = 0
    active: int = 0
    closed: int = 0
    cancelled: int = 0
    conversion_rate_pct: float = 0.0
    avg_time_to_assign_sec: float | None = None
    avg_time_to_close_sec: float | None = None


@dataclass
class ManagerMetrics:
    manager_id: str = ""
    manager_telegram_id: int | None = None
    assigned_leads: int = 0
    closed_leads: int = 0
    avg_response_sec: float | None = None
    sla_breaches: int = 0


@dataclass
class RevenueMetrics:
    gross_revenue: float = 0.0
    net_revenue: float = 0.0
    currency: str = "USD"
    deals_closed: int = 0
    revenue_per_manager: dict[str, float] = field(default_factory=dict)
    revenue_per_source: dict[str, float] = field(default_factory=dict)


class KpiCalculator:
    """Pure KPI helpers — scaffold. Wire to DB in migration phase."""

    @staticmethod
    def conversion_rate(closed: int, total: int) -> float:
        if total <= 0:
            return 0.0
        return round(closed / total * 100, 2)

    @staticmethod
    def build_lead_metrics(raw: dict[str, Any]) -> LeadMetrics:
        total = int(raw.get("total_leads") or 0)
        closed = int(raw.get("closed_leads") or 0)
        return LeadMetrics(
            total_leads=total,
            new_today=int(raw.get("new_leads_today") or 0),
            active=int(raw.get("active_leads") or 0),
            closed=closed,
            cancelled=int(raw.get("cancelled_leads") or 0),
            conversion_rate_pct=KpiCalculator.conversion_rate(closed, total),
            avg_time_to_assign_sec=raw.get("avg_time_to_assign_sec"),
            avg_time_to_close_sec=raw.get("avg_time_to_close_sec"),
        )

    @staticmethod
    async def from_owner_analytics() -> LeadMetrics:
        """Optional adapter to existing OwnerAnalyticsEngineV1 — not called by bot."""
        try:
            from services.pg_owner_analytics_engine import OwnerAnalyticsEngineV1

            data = await OwnerAnalyticsEngineV1.get_dashboard_metrics()
            return KpiCalculator.build_lead_metrics(data)
        except Exception:
            return LeadMetrics()
