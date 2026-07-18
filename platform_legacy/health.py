# Migration health — subsystem readiness for platform routing.

from __future__ import annotations

from typing import Any

from platform_legacy.migration_manager import MigrationState, migration_manager
from platform_legacy.registry import legacy_registry


def subsystem_health(subsystem: str) -> dict[str, Any]:
    record = migration_manager.get(subsystem)
    route = "legacy" if migration_manager.should_route_to_legacy(subsystem) else "platform"
    errors = legacy_registry.metrics.errors_by_adapter
    adapter_map = {
        "telegram": "telegram",
        "users": "permissions",
        "requests": "crm",
        "managers": "notification",
        "notifications": "notification",
        "workflow": "workflow_rules",
        "ai": "ai",
        "repositories": "workflow_rules",
        "configuration": "permissions",
        "scheduler": "scheduler",
    }
    adapter = adapter_map.get(subsystem)
    adapter_errors = errors.get(adapter, 0) if adapter else 0
    status = "healthy"
    if record.state == MigrationState.REMOVED and route == "legacy":
        status = "misconfigured"
    elif adapter_errors > 10:
        status = "degraded"
    return {
        "subsystem": subsystem,
        "state": record.state.value,
        "active_route": route,
        "status": status,
        "adapter_errors": adapter_errors,
    }


def migration_health() -> dict[str, Any]:
    checks = [subsystem_health(name) for name in migration_manager.list_subsystems()]
    unhealthy = [c for c in checks if c["status"] != "healthy"]
    return {
        "ok": not unhealthy,
        "checks": checks,
        "unhealthy_count": len(unhealthy),
    }
