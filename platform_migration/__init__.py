"""Enterprise Migration & Disaster Recovery — Sprint 25.4 / v8.4.0.

Design target: src/platform/migration → platform_migration.
Safe version upgrades with backup, restore, rollback and recovery validation — no data loss.
"""

from platform_migration.facade import MigrationLibrary, migration_library

__all__ = ["MigrationLibrary", "migration_library"]
