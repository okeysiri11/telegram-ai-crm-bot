# Activity widgets — recent events, audit, configuration changes, notifications.

from __future__ import annotations

from typing import Any

from platform_operations.models import SharedDashboardContext


async def _ensure_event_bus(ctx: SharedDashboardContext) -> dict[str, Any]:
    if ctx.event_bus is None:
        from platform_management.statistics import get_event_bus_overview

        ctx.event_bus = await get_event_bus_overview()
    return ctx.event_bus


async def _ensure_recent_audit(ctx: SharedDashboardContext, *, limit: int = 20) -> list[dict[str, Any]]:
    if not ctx.recent_audit:
        from platform_management.management_service import management_service

        ctx.recent_audit = await management_service.audit_search(limit=limit)
    return ctx.recent_audit


async def build_recent_events(ctx: SharedDashboardContext) -> dict[str, Any]:
    bus = await _ensure_event_bus(ctx)
    audit_rows = await _ensure_recent_audit(ctx, limit=15)

    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in audit_rows[:15]:
        etype = str(row.get("event_type") or "UNKNOWN")
        grouped.setdefault(etype, []).append(row)

    return {
        "platform_subscribers": bus.get("platform_subscribers", {}),
        "crm_queue": bus.get("crm_event_metrics", {}).get("queue", {}),
        "failed_deliveries": bus.get("failed_deliveries", 0),
        "latest_audit_events": audit_rows[:10],
        "grouped_by_type": grouped,
    }


async def build_recent_audit(ctx: SharedDashboardContext) -> dict[str, Any]:
    rows = await _ensure_recent_audit(ctx, limit=25)
    return {"entries": rows, "count": len(rows)}


async def build_configuration_changes(ctx: SharedDashboardContext) -> dict[str, Any]:
    if not ctx.config_changes:
        from platform_management.management_service import management_service

        ctx.config_changes = await management_service.audit_search(
            event_type="CONFIGURATION_CHANGED",
            limit=20,
        )
    return {"changes": ctx.config_changes, "count": len(ctx.config_changes)}


async def build_notifications_queue(ctx: SharedDashboardContext) -> dict[str, Any]:
    bus = await _ensure_event_bus(ctx)
    queue = bus.get("crm_event_metrics", {}).get("queue", {})
    from platform_configuration.config_provider import config_provider

    return {
        "pending": queue.get("pending", 0),
        "failed": queue.get("failed", 0),
        "dead_letter": queue.get("dead_letter", 0),
        "notifications_enabled": config_provider.is_notification_enabled(),
    }
