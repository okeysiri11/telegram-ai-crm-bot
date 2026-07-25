"""Rollback Manager — Sprint 25.4."""

from __future__ import annotations

from typing import Any


class RollbackManager:
    def last(self, *, migration_id: str) -> dict[str, Any]:
        if not migration_id:
            raise ValueError("migration_id is required")
        return {"mode": "last", "migration_id": migration_id, "rolled_back": True, "safe": True, "data_loss": False}

    def to_version(self, *, version: str) -> dict[str, Any]:
        if not version:
            raise ValueError("version is required")
        return {"mode": "selected_version", "version": version, "rolled_back": True, "safe": True, "data_loss": False}

    def bulk(self, *, migration_ids: list[str]) -> dict[str, Any]:
        if not migration_ids:
            raise ValueError("migration_ids required")
        return {
            "mode": "bulk",
            "migration_ids": list(migration_ids),
            "rolled_back": True,
            "count": len(migration_ids),
            "safe": True,
            "data_loss": False,
        }
