# Zero Trust continuous evaluation — extends Sprint 21.4 ZeroTrustEngine.

from __future__ import annotations

from typing import Any

from platform_security.models import ZERO_TRUST_CHECKS


class ZeroTrustEngine:
    """Never trust by default — verify identity, permissions, and context every request."""

    PRINCIPLES = (
        "verify_explicitly",
        "least_privilege",
        "assume_breach",
        "continuous_validation",
        "never_trust_internal_by_default",
    )

    def evaluate(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        ctx = context or {}
        checks: dict[str, Any] = {}
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
            "principles": list(self.PRINCIPLES),
        }

    def evaluate_continuous(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Continuous validation: base checks + permission + tenant + session integrity."""
        base = self.evaluate(context)
        ctx = context or {}
        extras: dict[str, Any] = {}

        # Permission / role presence (RBAC surface — ISAM / permission_engine enforce).
        roles = ctx.get("roles") or ctx.get("permissions")
        extras["authorization"] = {
            "present": roles is not None,
            "passed": bool(roles) if "roles" in ctx or "permissions" in ctx else True,
        }

        tenant = ctx.get("tenant_id") or ctx.get("organization_id")
        require_tenant = bool(ctx.get("require_tenant"))
        extras["tenant_isolation"] = {
            "present": tenant is not None or not require_tenant,
            "passed": bool(tenant) if require_tenant else True,
        }

        session_ok = ctx.get("session_valid")
        if session_ok is None:
            session_ok = bool(ctx.get("token"))
        extras["session_integrity"] = {"present": True, "passed": bool(session_ok)}

        # Device trust (optional MFA / trusted device).
        if "trusted_device" in ctx:
            extras["trusted_device"] = {
                "present": True,
                "passed": bool(ctx.get("trusted_device")),
            }

        all_checks = {**base["checks"], **extras}
        passed = all(c["passed"] for c in all_checks.values())
        score = round(sum(1 for c in all_checks.values() if c["passed"]) / max(1, len(all_checks)), 3)
        return {
            "allowed": passed,
            "trust_score": score,
            "checks": all_checks,
            "dimensions": list(all_checks.keys()),
            "principles": list(self.PRINCIPLES),
            "mode": "continuous",
            "zero_trust": True,
        }

    def policy(self) -> dict[str, Any]:
        return {
            "model": "zero_trust",
            "principles": list(self.PRINCIPLES),
            "checks": list(ZERO_TRUST_CHECKS),
            "continuous": True,
            "sprint": "32.4",
        }
