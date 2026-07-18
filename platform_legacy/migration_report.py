# Migration report — full transition status for operations and CI.

from __future__ import annotations

from typing import Any

from platform_legacy.coverage import migration_coverage
from platform_legacy.deprecation import list_registered_deprecations
from platform_legacy.deprecation_manager import deprecation_manager
from platform_legacy.feature_flags import load_legacy_migration_flags
from platform_legacy.health import migration_health
from platform_legacy.migration_manager import MigrationState, migration_manager
from platform_legacy.registry import legacy_registry
from platform_legacy.runtime_monitor import runtime_monitor


def build_migration_status() -> dict[str, Any]:
    snapshot = migration_manager.snapshot()
    return {
        "platform_default": True,
        "platform_routed_percent": snapshot["platform_percent"],
        "subsystems": snapshot["subsystems"],
        "history": snapshot["history"],
    }


def build_coverage_report() -> dict[str, Any]:
    report = migration_coverage.coverage_report()
    monitor = runtime_monitor.snapshot()
    legacy_freq = legacy_registry.metrics.calls_by_adapter
    return {
        **report,
        "runtime": monitor,
        "legacy_call_frequency": dict(legacy_freq),
        "deprecated_api_hits": dict(legacy_registry.metrics.deprecated_api_hits),
    }


def build_migration_report() -> dict[str, Any]:
    """Comprehensive migration / deprecation report."""
    flags = load_legacy_migration_flags()
    manager_snapshot = migration_manager.snapshot()
    registry_snapshot = legacy_registry.snapshot()
    coverage = build_coverage_report()
    remaining = [
        name
        for name, rec in manager_snapshot["subsystems"].items()
        if rec["state"] in {MigrationState.LEGACY.value, MigrationState.MIGRATING.value}
    ]
    return {
        "summary": {
            "platform_default": True,
            "legacy_compatibility_mode": "enabled_via_flags",
            "platform_routed_percent": manager_snapshot["platform_percent"],
            "runtime_platform_percent": coverage.get("migration_percent", 0),
            "migration_percent": coverage.get("migration_percent", 0),
            "isolation_enforced": registry_snapshot["migration"]["isolation_enforced"],
            "total_legacy_calls": registry_snapshot["metrics"]["total_calls"],
            "total_legacy_errors": registry_snapshot["metrics"]["total_errors"],
            "remaining_legacy_count": len(remaining),
        },
        "migrated_components": coverage.get("migrated_components", []),
        "remaining_legacy": remaining,
        "subsystems": manager_snapshot["subsystems"],
        "migration_history": manager_snapshot["history"],
        "feature_flags": flags.to_dict(),
        "coverage": coverage,
        "deprecated_apis": deprecation_manager.list_deprecated(),
        "registered_deprecations": list_registered_deprecations(),
        "adapter_metrics": registry_snapshot["metrics"],
        "adapters": registry_snapshot["adapters"],
        "health": migration_health(),
        "runtime": runtime_monitor.snapshot(),
    }
