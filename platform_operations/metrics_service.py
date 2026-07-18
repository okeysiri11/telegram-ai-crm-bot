# KPI metrics widget — delegates to KPI service (day/week/month).

from __future__ import annotations

from typing import Any, Literal

from platform_operations.models import SharedDashboardContext

KpiPeriod = Literal["day", "week", "month"]


async def _kpi(ctx: SharedDashboardContext, period: KpiPeriod) -> dict[str, Any]:
    if period == "day":
        if ctx.kpi_day is None:
            from services.kpi_service import kpi_service

            ctx.kpi_day = await kpi_service.get_platform_kpi(period="day")
        return ctx.kpi_day
    if period == "week":
        if ctx.kpi_week is None:
            from services.kpi_service import kpi_service

            ctx.kpi_week = await kpi_service.get_platform_kpi(period="week")
        return ctx.kpi_week
    if ctx.kpi_month is None:
        from services.kpi_service import kpi_service

        ctx.kpi_month = await kpi_service.get_platform_kpi(period="month")
    return ctx.kpi_month


def _totals(kpi: dict[str, Any]) -> dict[str, Any]:
    totals = kpi.get("totals") or {}
    return totals if isinstance(totals, dict) else {}


async def build_top_kpis(ctx: SharedDashboardContext) -> dict[str, Any]:
    day = await _kpi(ctx, "day")
    week = await _kpi(ctx, "week")
    month = await _kpi(ctx, "month")

    month_totals = _totals(month)
    return {
        "today": _totals(day),
        "week": _totals(week),
        "month": month_totals,
        "average_response_seconds": month_totals.get("average_response_time_seconds"),
        "average_resolution_seconds": month_totals.get("average_resolution_time_seconds"),
        "manager_rankings": month.get("manager_rankings", [])[:5],
        "by_vertical": month.get("by_vertical", {}),
    }


async def build_metrics(*, period: KpiPeriod = "month", ctx: SharedDashboardContext | None = None) -> dict[str, Any]:
    shared = ctx or SharedDashboardContext()
    kpi = await _kpi(shared, period)
    totals = _totals(kpi)
    return {
        "period": period,
        "totals": totals,
        "average_response_seconds": totals.get("average_response_time_seconds"),
        "average_resolution_seconds": totals.get("average_resolution_time_seconds"),
        "sla_compliance_rate": totals.get("sla_compliance_rate"),
        "by_vertical": kpi.get("by_vertical", {}),
        "manager_rankings": kpi.get("manager_rankings", []),
    }
