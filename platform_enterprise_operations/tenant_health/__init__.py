"""Tenant Health Monitor — Sprint 23.0."""

from __future__ import annotations

from typing import Any

from platform_enterprise_operations.models import TENANT_HEALTH_DIMS


class TenantHealthMonitor:
    def score(self, *, company_id: str, dimensions: dict[str, Any] | None = None, errors: list[str] | None = None, warnings: list[str] | None = None, performance: float = 1.0) -> dict[str, Any]:
        if not company_id:
            raise ValueError("company_id is required")
        dimensions = dict(dimensions or {})
        dims = {}
        for d in TENANT_HEALTH_DIMS:
            val = float(dimensions.get(d, 1.0))
            dims[d] = max(0.0, min(1.0, val))
        errors = list(errors or [])
        warnings = list(warnings or [])
        perf = max(0.0, min(1.0, float(performance)))
        base = sum(dims.values()) / len(dims)
        penalty = min(0.5, 0.05 * len(errors) + 0.02 * len(warnings))
        health = max(0.0, round((base * 0.8 + perf * 0.2) - penalty, 3))
        return {
            "company_id": company_id,
            "dimensions": dims,
            "errors": errors,
            "warnings": warnings,
            "performance": perf,
            "health_score": health,
            "status": "healthy" if health >= 0.8 else ("degraded" if health >= 0.5 else "critical"),
        }
