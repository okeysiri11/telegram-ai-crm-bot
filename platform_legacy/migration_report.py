# Migration report — full transition status for operations and CI.

from __future__ import annotations

from typing import Any

from platform_legacy.coverage import migration_coverage
from platform_legacy.deprecation_manager import deprecation_manager
from platform_legacy.feature_flags import load_legacy_migration_flags
from platform_legacy.health import migration_health
from platform_legacy.migration_manager import migration_manager
from platform_legacy.registry import legacy_registry


def build_migration_report() -> dict[str, Any]:
    """Comprehensive migration / deprecation report."""
    flags = load_legacy_migration_flags()
    manager_snapshot = migration_manager.snapshot()
    registry_snapshot = legacy_registry.snapshot()
    return {
        "summary": {
            "platform_default": True,
            "legacy_compatibility_mode": "enabled_via_flags",
            "platform_routed_percent": manager_snapshot["platform_percent"],
            "isolation_enforced": registry_snapshot["migration"]["isolation_enforced"],
            "total_legacy_calls": registry_snapshot["metrics"]["total_calls"],
            "total_legacy_errors": registry_snapshot["metrics"]["total_errors"],
        },
        "subsystems": manager_snapshot["subsystems"],
        "migration_history": manager_snapshot["history"],
        "feature_flags": flags.to_dict(),
        "coverage": migration_coverage.to_dict(),
        "deprecated_apis": deprecation_manager.list_deprecated(),
        "adapter_metrics": registry_snapshot["metrics"],
        "adapters": registry_snapshot["adapters"],
        "health": migration_health(),
    }
