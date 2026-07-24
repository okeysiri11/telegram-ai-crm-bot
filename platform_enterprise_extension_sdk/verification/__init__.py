"""Verification Pipeline — Sprint 25.0."""

from __future__ import annotations

from typing import Any

from platform_enterprise_extension_sdk.models import VERIFICATION_CHECKS


class VerificationPipeline:
    def run(self, *, extension: dict[str, Any], fail_check: str | None = None) -> dict[str, Any]:
        if not extension.get("extension_id"):
            raise ValueError("extension_id is required")
        results = []
        for check in VERIFICATION_CHECKS:
            ok = check != fail_check
            results.append({"check": check, "passed": ok})
        all_ok = all(r["passed"] for r in results)
        signature = None
        if all_ok:
            signature = f"sig_{extension['extension_id']}_{extension.get('version', '1')}"
        return {
            "extension_id": extension["extension_id"],
            "checks": results,
            "passed": all_ok,
            "signature": signature,
            "status": "verified" if all_ok else "testing",
        }
