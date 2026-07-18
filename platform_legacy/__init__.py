# platform_legacy — strict isolation boundary for legacy Telegram CRM.

from platform_legacy.compatibility_layer import compatibility_layer
from platform_legacy.deprecation import deprecated
from platform_legacy.deprecation_manager import deprecation_manager
from platform_legacy.facade import legacy
from platform_legacy.legacy_import_policy import scan_legacy_import_violations
from platform_legacy.migration_manager import MigrationState, migration_manager
from platform_legacy.migration_report import build_migration_report
from platform_legacy.registry import legacy_registry
from platform_legacy.runtime_monitor import runtime_monitor

__all__ = [
    "legacy",
    "legacy_registry",
    "scan_legacy_import_violations",
    "migration_manager",
    "MigrationState",
    "compatibility_layer",
    "deprecation_manager",
    "deprecated",
    "build_migration_report",
    "runtime_monitor",
]
