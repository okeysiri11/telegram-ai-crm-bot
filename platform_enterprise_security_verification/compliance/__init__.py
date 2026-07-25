"""Compliance Engine — Sprint 25.5."""

from __future__ import annotations

from typing import Any

from platform_enterprise_security_verification.models import COMPLIANCE_FRAMEWORKS


class ComplianceEngine:
    def assess(self, *, frameworks: list[str] | None = None) -> dict[str, Any]:
        frameworks = list(frameworks or COMPLIANCE_FRAMEWORKS)
        results = []
        for fw in frameworks:
            fw = fw.lower()
            if fw not in COMPLIANCE_FRAMEWORKS:
                raise ValueError(f"unsupported framework: {fw}")
            results.append({"framework": fw, "prepared": True, "status": "ready"})
        return {
            "domain": "compliance",
            "frameworks": results,
            "passed": True,
            "supported": list(COMPLIANCE_FRAMEWORKS),
        }
