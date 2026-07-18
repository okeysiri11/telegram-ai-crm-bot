# Management statistics — aggregates platform metrics (delegates only).

from __future__ import annotations

from typing import Any

from models.manager_kpi import KpiPeriod


async def get_request_statistics() -> dict[str, Any]:
    from services.sla_dashboard_service import sla_dashboard_service

    stats = await sla_dashboard_service.get_statistics()
    overdue = await sla_dashboard_service.get_overdue(limit=20)
    at_risk = await sla_dashboard_service.get_at_risk(limit=20)
    return {
        "summary": stats,
        "open_queues": {
            "overdue_sample": overdue,
            "at_risk_sample": at_risk,
        },
        "sla_violations": stats.get("overdue_count", stats.get("overdue", 0)),
    }


async def get_kpi_dashboard(*, period: KpiPeriod = "month") -> dict[str, Any]:
    from services.kpi_service import kpi_service

    platform = await kpi_service.get_platform_kpi(period=period)
    return {
        "period": period,
        "platform": platform,
        "top_managers": platform.get("manager_rankings", [])[:10],
        "sla_statistics": platform.get("totals", {}),
        "charts": {
            "by_vertical": platform.get("by_vertical", {}),
            "totals": platform.get("totals", {}),
        },
        "aggregations": platform.get("totals", {}),
    }


async def get_event_bus_overview() -> dict[str, Any]:
    from events.event_bus import PlatformEventBus
    from services.event_bus_metrics import get_metrics

    crm_metrics = await get_metrics()
    return {
        "platform_subscribers": PlatformEventBus.list_subscribers(),
        "crm_event_metrics": crm_metrics,
        "failed_deliveries": crm_metrics.get("queue", {}).get("failed", 0),
        "dead_letter": crm_metrics.get("queue", {}).get("dead_letter", 0),
    }
