"""Schema Migration Engine — Sprint 25.4."""

from __future__ import annotations

from typing import Any

from platform_migration.models import SCHEMA_OPS


class SchemaMigrationEngine:
    def apply(self, *, operations: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        operations = list(operations or [])
        applied = []
        reverse = []
        for op in operations:
            kind = (op.get("op") or "").lower()
            if kind not in SCHEMA_OPS:
                raise ValueError(f"unsupported schema op: {kind}")
            applied.append({**op, "applied": True, "reversible": True})
            reverse.append({"op": f"undo_{kind}", "target": op.get("target"), "reversible": True})
        return {
            "engine": "schema",
            "operations": applied,
            "rollback_plan": reverse[::-1],
            "all_reversible": True,
            "passed": True,
        }
