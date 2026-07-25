"""Deployment Validator — Sprint 25.6."""

from __future__ import annotations

from typing import Any

from platform_enterprise_production.models import DEPLOYMENT_CHECKS


class DeploymentValidator:
    def validate(self, *, failed: list[str] | None = None) -> dict[str, Any]:
        failed = set(failed or [])
        checks = []
        for name in DEPLOYMENT_CHECKS:
            ok = name not in failed
            checks.append({
                "check": name,
                "passed": ok,
                "integrates": {
                    "migrations": "migration",
                    "backups": "migration",
                    "security": "security_verification",
                    "performance": "performance_testing",
                    "fault_tolerance": "chaos_engineering",
                    "tests": "test_infrastructure",
                    "version_compatibility": "migration",
                }.get(name),
            })
        passed = all(c["passed"] for c in checks)
        return {
            "checks": checks,
            "passed": passed,
            "blocks_release": not passed,
            "required_before_production": True,
        }
