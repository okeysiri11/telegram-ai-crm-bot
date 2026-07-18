# Request and manager summary widgets — delegates to SLA, KPI, manager pool services.

from __future__ import annotations

from typing import Any

from platform_operations.models import SharedDashboardContext


async def _ensure_sla(ctx: SharedDashboardContext) -> dict[str, Any]:
    if ctx.sla_stats is None:
        from services.sla_dashboard_service import sla_dashboard_service

        ctx.sla_stats = await sla_dashboard_service.get_statistics()
    return ctx.sla_stats


async def build_active_requests(ctx: SharedDashboardContext) -> dict[str, Any]:
    stats = await _ensure_sla(ctx)
    from services.sla_dashboard_service import sla_dashboard_service

    overdue_sample = await sla_dashboard_service.get_overdue(limit=10)
    escalated = await sla_dashboard_service.get_owner_escalated(limit=10)

    return {
        "current_open": stats.get("active", 0),
        "completed_today": stats.get("completed_today", 0),
        "overdue": stats.get("overdue", 0),
        "at_risk": stats.get("risk", 0),
        "escalated_count": len(escalated),
        "overdue_sample": overdue_sample,
        "escalated_sample": escalated,
    }


async def build_requests_by_vertical(ctx: SharedDashboardContext) -> dict[str, Any]:
    if ctx.kpi_month is None:
        from services.kpi_service import kpi_service

        ctx.kpi_month = await kpi_service.get_platform_kpi(period="month")

    by_vertical = ctx.kpi_month.get("by_vertical") or {}
    grouped: list[dict[str, Any]] = []
    if isinstance(by_vertical, dict):
        for code, metrics in by_vertical.items():
            grouped.append(
                {"vertical": code, **(metrics if isinstance(metrics, dict) else {"value": metrics})}
            )
    elif isinstance(by_vertical, list):
        grouped = by_vertical

    return {"grouped_by_vertical": grouped, "period": "month"}


async def build_sla_status(ctx: SharedDashboardContext) -> dict[str, Any]:
    stats = await _ensure_sla(ctx)
    return {
        "active": stats.get("active", 0),
        "overdue": stats.get("overdue", 0),
        "at_risk": stats.get("risk", 0),
        "completed_today": stats.get("completed_today", 0),
        "avg_response_minutes": stats.get("avg_response_minutes"),
        "owner_escalations_today": stats.get(
            "owner_escalations_today",
            stats.get("owner_escalated_today"),
        ),
    }


async def build_manager_load(ctx: SharedDashboardContext) -> dict[str, Any]:
    await _ensure_sla(ctx)

    if ctx.pool_dashboard is None:
        from services.manager_pool_service import manager_pool_service

        ctx.pool_dashboard = await manager_pool_service.get_pool_dashboard()

    if ctx.assignment_stats is None:
        from services.smart_assignment_service import smart_assignment_service

        ctx.assignment_stats = await smart_assignment_service.get_statistics()

    if ctx.kpi_month is None:
        from services.kpi_service import kpi_service

        ctx.kpi_month = await kpi_service.get_platform_kpi(period="month")

    pool = ctx.pool_dashboard
    kpi = pool.get("kpi") or {}
    rankings = ctx.kpi_month.get("manager_rankings") or []
    top = rankings[0] if rankings else None

    active = len(pool.get("managers") or [])
    busy = kpi.get("busy_managers", 0)
    idle = kpi.get("idle_managers", 0)

    return {
        "active_managers": active,
        "busy_managers": busy,
        "available_managers": idle,
        "current_load": kpi.get("manager_current_load", {}),
        "average_load": kpi.get("manager_average_load"),
        "average_sla_minutes": ctx.sla_stats.get("avg_response_minutes") if ctx.sla_stats else None,
        "top_performer": top,
        "assignment_strategy": pool.get("assignment_mode"),
        "assignment_statistics": ctx.assignment_stats,
    }
