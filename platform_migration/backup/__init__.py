"""Backup Manager — Sprint 25.4."""

from __future__ import annotations

from typing import Any

from platform_migration.models import BACKUP_KINDS


class BackupManager:
    def create(self, *, kind: str, label: str = "") -> dict[str, Any]:
        kind = (kind or "").lower()
        if kind not in BACKUP_KINDS:
            raise ValueError(f"unsupported backup kind: {kind}")
        return {
            "backup_id": f"bak_{kind}_{label or 'auto'}",
            "kind": kind,
            "label": label or "auto",
            "created": True,
            "encrypted": kind == "secrets",
            "restorable": True,
            "kinds": list(BACKUP_KINDS),
        }

    def create_all(self, *, label: str = "pre_migrate") -> dict[str, Any]:
        items = [self.create(kind=k, label=label) for k in BACKUP_KINDS]
        return {"backups": items, "count": len(items), "automatic": True, "complete": True}
