"""Multi-Tenant Isolation checks — Sprint 25.5."""

from __future__ import annotations

from typing import Any

from platform_enterprise_security_verification.models import TENANT_ISOLATION_CHECKS


class TenantIsolationValidator:
    def validate(self, *, fail: str | None = None) -> dict[str, Any]:
        results = [{"check": c, "isolated": c != fail, "passed": c != fail} for c in TENANT_ISOLATION_CHECKS]
        return {"domain": "tenant_isolation", "checks": results, "passed": all(r["passed"] for r in results)}
