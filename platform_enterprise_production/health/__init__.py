"""Health Check Engine — Sprint 25.6."""

from __future__ import annotations

from typing import Any

from platform_enterprise_production.models import HEALTH_TARGETS


class HealthCheckEngine:
    def check(self, *, failed: list[str] | None = None) -> dict[str, Any]:
        failed = set(failed or [])
        checks = []
        for target in HEALTH_TARGETS:
            ok = target not in failed
            checks.append({
                "target": target,
                "status": "healthy" if ok else "unhealthy",
                "passed": ok,
                "continuous": True,
            })
        passed = all(c["passed"] for c in checks)
        return {
            "checks": checks,
            "passed": passed,
            "continuous": True,
            "unhealthy": [c["target"] for c in checks if not c["passed"]],
            "blocks_release": not passed,
        }
