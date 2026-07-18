# System and workflow status widgets — delegates to Management API probes.

from __future__ import annotations

from typing import Any

from platform_operations.models import SharedDashboardContext


async def build_system_status(ctx: SharedDashboardContext) -> dict[str, Any]:
    from platform_management.health import get_health_snapshot
    from platform_management.system_info import get_component_statuses, get_system_info

    if ctx.system_info is None:
        ctx.system_info = await get_system_info()
    if ctx.health is None:
        ctx.health = await get_health_snapshot()

    components = await get_component_statuses()
    info = ctx.system_info
    health = ctx.health

    def _status(key: str) -> str:
        item = components.get(key, {})
        if isinstance(item, dict):
            return str(item.get("status", "unknown"))
        return str(item)

    return {
        "postgresql": components.get("database", {}),
        "redis": components.get("redis", {}),
        "sdk": components.get("sdk", {}),
        "workflow_engine": components.get("workflow", {}),
        "configuration": components.get("configuration", {}),
        "event_bus": health.get("event_bus", {}),
        "assignment_engine": health.get("assignment_engine", {}),
        "notifications": components.get("notifications", {}),
        "health": health.get("overall_status", "unknown"),
        "version": info.get("platform_version"),
        "uptime_seconds": info.get("uptime_seconds"),
        "build_version": info.get("build_version"),
        "git_revision": info.get("git_revision"),
        "environment": info.get("environment"),
        "component_status": {
            "postgresql": _status("database"),
            "redis": _status("redis"),
            "sdk": _status("sdk"),
            "workflow": _status("workflow"),
            "configuration": _status("configuration"),
        },
    }


async def build_platform_version(ctx: SharedDashboardContext) -> dict[str, Any]:
    from platform_management.system_info import get_system_info

    if ctx.system_info is None:
        ctx.system_info = await get_system_info()
    info = ctx.system_info
    return {
        "platform_version": info.get("platform_version"),
        "build_version": info.get("build_version"),
        "git_revision": info.get("git_revision"),
        "environment": info.get("environment"),
        "uptime_seconds": info.get("uptime_seconds"),
    }


async def build_workflow_status(ctx: SharedDashboardContext) -> dict[str, Any]:
    if ctx.workflow_stats is None:
        from workflow.workflow_engine import workflow_engine

        ctx.workflow_stats = await workflow_engine.get_statistics()

    stats = ctx.workflow_stats
    registered = stats.get("registered_workflows") or []
    return {
        "loaded_workflows": len(registered),
        "workflows": registered,
        "running": stats.get("active_executions", 0),
        "completed_today": stats.get("completed_today", 0),
        "errors": stats.get("failed_today", 0),
        "reload_time": stats.get("last_reload_at"),
        "average_execution_time_ms": stats.get("average_execution_time_ms"),
        "kpi": stats.get("kpi", {}),
    }
