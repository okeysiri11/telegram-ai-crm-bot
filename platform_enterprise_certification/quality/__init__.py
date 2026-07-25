"""Quality Gate — Sprint 25.7."""

from __future__ import annotations

from typing import Any

from platform_enterprise_certification.models import QUALITY_GATES


class QualityGate:
    def evaluate(self, *, failed: list[str] | None = None) -> dict[str, Any]:
        failed = set(failed or [])
        gates = []
        for name in QUALITY_GATES:
            ok = name not in failed
            gates.append({
                "gate": name,
                "passed": ok,
                "critical": True,
                "integrates": {
                    "unit_tests": "test_infrastructure",
                    "integration_tests": "test_infrastructure",
                    "smoke_tests": "test_infrastructure",
                    "regression_tests": "test_infrastructure",
                    "performance_tests": "performance_testing",
                    "chaos_tests": "chaos_engineering",
                    "security_verification": "security_verification",
                    "migration_verification": "migration",
                    "production_readiness": "production_readiness",
                }.get(name),
            })
        passed = all(g["passed"] for g in gates)
        return {
            "gates": gates,
            "passed": passed,
            "failed": [g["gate"] for g in gates if not g["passed"]],
            "blocks_release": not passed,
        }
