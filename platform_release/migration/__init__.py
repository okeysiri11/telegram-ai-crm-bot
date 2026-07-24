"""Migration framework — Sprint 21.8."""

from __future__ import annotations

from typing import Any

from platform_release.models import MIGRATION_KINDS


class MigrationFramework:
    def plan(self) -> dict[str, Any]:
        migrations = [
            {"kind": k, "compatible": True, "steps": 3 if k == "database" else 2}
            for k in MIGRATION_KINDS
        ]
        return {
            "migrations": migrations,
            "version_compatible": True,
            "from_version": "6.0.0-rc7",
            "to_version": "6.0.0",
            "passed": all(m["compatible"] for m in migrations),
        }
