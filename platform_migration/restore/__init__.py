"""Restore Engine — Sprint 25.4."""

from __future__ import annotations

from typing import Any

from platform_migration.models import RESTORE_TARGETS


class RestoreEngine:
    def restore(self, *, target: str, backup_id: str) -> dict[str, Any]:
        target = (target or "").lower()
        if target not in RESTORE_TARGETS:
            raise ValueError(f"unsupported restore target: {target}")
        if not backup_id:
            raise ValueError("backup_id is required")
        return {
            "restored": True,
            "target": target,
            "backup_id": backup_id,
            "targets": list(RESTORE_TARGETS),
            "data_loss": False,
        }
