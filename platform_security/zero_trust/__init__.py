"""Zero Trust evaluation — Sprint 21.4."""

from __future__ import annotations

from typing import Any

from platform_security.models import ZERO_TRUST_CHECKS


class ZeroTrustEngine:
    def evaluate(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = context or {}
        checks = {}
        for name in ZERO_TRUST_CHECKS:
            value = ctx.get(name)
            if name == "risk_level":
                checks[name] = {"present": value is not None, "passed": float(value or 0) < 0.7}
            else:
                checks[name] = {"present": bool(value), "passed": bool(value)}
        passed = all(c["passed"] for c in checks.values())
        score = round(sum(1 for c in checks.values() if c["passed"]) / len(checks), 3)
        return {
            "allowed": passed,
            "trust_score": score,
            "checks": checks,
            "dimensions": list(ZERO_TRUST_CHECKS),
        }
