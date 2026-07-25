"""Migration Dashboard — Sprint 25.4."""

from __future__ import annotations

from typing import Any


class MigrationDashboard:
    def render(
        self,
        *,
        current_version: str = "",
        queue: list[dict[str, Any]] | None = None,
        history: list[dict[str, Any]] | None = None,
        backup_status: str = "ok",
        restore_status: str = "idle",
        rollback_status: str = "available",
        recovery_validation: dict[str, Any] | None = None,
        failed: list[str] | None = None,
        recovery_time_ms: int = 0,
        health_status: str = "healthy",
    ) -> dict[str, Any]:
        return {
            "current_version": current_version,
            "migration_queue": list(queue or []),
            "migration_history": list(history or []),
            "backup_status": backup_status,
            "restore_status": restore_status,
            "rollback_status": rollback_status,
            "recovery_validation": dict(recovery_validation or {}),
            "failed_migrations": list(failed or []),
            "recovery_time_ms": int(recovery_time_ms),
            "health_status": health_status,
            "ci_cd_required": True,
        }
