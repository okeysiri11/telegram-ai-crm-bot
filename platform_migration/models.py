"""Migration & DR constants — Sprint 25.4."""

from __future__ import annotations

MIGRATION_STATUSES = (
    "pending",
    "running",
    "completed",
    "failed",
    "rolled_back",
    "validated",
)

SCHEMA_OPS = (
    "create_table",
    "alter_table",
    "alter_column",
    "create_index",
    "add_constraint",
    "add_foreign_key",
    "create_view",
    "create_trigger",
)

DATA_OPS = (
    "transfer",
    "transform_structure",
    "change_format",
    "merge",
    "split",
    "integrity_check",
)

BACKUP_KINDS = (
    "full",
    "incremental",
    "database",
    "object_storage",
    "configuration",
    "secrets",
)

RESTORE_TARGETS = (
    "platform",
    "module",
    "database",
    "files",
    "configuration",
    "ai_settings",
)

DR_SCENARIOS = (
    "database_loss",
    "data_corruption",
    "disk_failure",
    "configuration_loss",
    "file_deletion",
    "upgrade_failure",
    "emergency_rollback",
    "full_outage_recovery",
)

VALIDATION_CHECKS = (
    "data_integrity",
    "record_counts",
    "indexes",
    "relations",
    "users",
    "permissions",
    "workflows",
    "ai_providers",
    "marketplace",
    "enterprise_hub",
)

REPORT_KINDS = (
    "migration",
    "backup",
    "restore",
    "rollback",
    "recovery",
    "integrity",
)

INTEGRATION_TARGETS = (
    "enterprise_hub",
    "performance_testing",
    "chaos_engineering",
    "observability",
    "communications",
    "test_infrastructure",
)

KPI_TARGETS = {
    "safe_version_upgrades": True,
    "automatic_backups": True,
    "full_rollback_support": True,
    "disaster_recovery": True,
    "auto_integrity_checks": True,
    "migration_history": True,
    "no_data_loss": True,
}

PRINCIPLES = (
    "backup_before_migrate",
    "reversible_schema_ops",
    "validate_after_restore",
    "no_data_loss",
    "ci_cd_migration_gate",
    "no_duplicated_business_logic",
)
