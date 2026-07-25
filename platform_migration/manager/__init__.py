"""Migration Manager — Sprint 25.4."""

from __future__ import annotations

from typing import Any

from platform_migration.models import MIGRATION_STATUSES


class MigrationManager:
    def create(
        self,
        *,
        migration_id: str,
        version_from: str,
        version_to: str,
        module: str,
        author: str = "system",
        created_date: str = "now",
        dependencies: list[str] | None = None,
        rollback_support: bool = True,
        validation_rules: list[str] | None = None,
        status: str = "pending",
    ) -> dict[str, Any]:
        if not migration_id or not version_from or not version_to or not module:
            raise ValueError("migration_id, version_from, version_to and module are required")
        status = (status or "pending").lower()
        if status not in MIGRATION_STATUSES:
            raise ValueError(f"unsupported status: {status}")
        if not rollback_support:
            raise ValueError("rollback_support is required for safe migrations")
        return {
            "migration_id": migration_id,
            "version_from": version_from,
            "version_to": version_to,
            "module": module,
            "author": author,
            "created_date": created_date,
            "dependencies": list(dependencies or []),
            "rollback_support": True,
            "validation_rules": list(validation_rules or ["integrity", "no_data_loss"]),
            "status": status,
        }

    def set_status(self, migration: dict[str, Any], *, status: str) -> dict[str, Any]:
        status = (status or "").lower()
        if status not in MIGRATION_STATUSES:
            raise ValueError(f"unsupported status: {status}")
        updated = dict(migration)
        updated["status"] = status
        return updated
