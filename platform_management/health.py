# Management health aggregation — delegates to existing probes.

from __future__ import annotations

from typing import Any

from events.event_bus import PlatformEventBus


async def get_health_snapshot() -> dict[str, Any]:
    from database.session import check_db_health
    from platform_management.system_info import get_component_statuses
    from services.sla_dashboard_service import sla_dashboard_service
    from services.smart_assignment_service import smart_assignment_service
    from workflow.workflow_engine import workflow_engine

    components = await get_component_statuses()

    overall = "healthy"
    for key, value in components.items():
        status = value.get("status") if isinstance(value, dict) else value
        if status in {"unhealthy", "OFFLINE", "offline"}:
            overall = "unhealthy"
            break
        if status in {"degraded", "DEGRADED", "degraded"} and overall == "healthy":
            overall = "degraded"

    return {
        "overall_status": overall,
        "postgresql": components.get("database", {}),
        "redis": components.get("redis", {}),
        "event_bus": {
            "status": "healthy",
            "subscribers": PlatformEventBus.list_subscribers(),
        },
        "workflow_engine": await _safe(workflow_engine.get_statistics, default={"status": "unknown"}),
        "notification_service": components.get("notifications", {"status": "unknown"}),
        "assignment_engine": await _safe(smart_assignment_service.get_statistics, default={}),
        "dashboard": await _safe(sla_dashboard_service.get_statistics, default={}),
        "configuration_center": components.get("configuration", {"status": "unknown"}),
        "database_probe": await check_db_health(),
    }


async def _safe(coro_factory, *, default: Any) -> Any:
    try:
        result = coro_factory()
        if hasattr(result, "__await__"):
            return await result
        return result
    except Exception as exc:
        return {"status": "degraded", "error": str(exc), **default}
