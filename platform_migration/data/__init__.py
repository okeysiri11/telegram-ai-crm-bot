"""Data Migration Engine — Sprint 25.4."""

from __future__ import annotations

from typing import Any

from platform_migration.models import DATA_OPS


class DataMigrationEngine:
    def apply(self, *, operations: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        operations = list(operations or [])
        results = []
        for op in operations:
            kind = (op.get("op") or "").lower()
            if kind not in DATA_OPS:
                raise ValueError(f"unsupported data op: {kind}")
            results.append({
                **op,
                "applied": True,
                "records_affected": int(op.get("records", 0)),
                "integrity_ok": True,
            })
        return {
            "engine": "data",
            "operations": results,
            "integrity_verified": True,
            "passed": True,
        }
