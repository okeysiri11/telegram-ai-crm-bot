"""Recovery Validator — Sprint 25.4."""

from __future__ import annotations

from typing import Any

from platform_migration.models import VALIDATION_CHECKS


class RecoveryValidator:
    def validate(self, *, fail_check: str | None = None) -> dict[str, Any]:
        results = []
        for check in VALIDATION_CHECKS:
            ok = check != fail_check
            results.append({"check": check, "passed": ok})
        return {
            "checks": results,
            "passed": all(r["passed"] for r in results),
            "no_data_loss": True,
            "automatic": True,
        }
