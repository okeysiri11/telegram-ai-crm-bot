"""Vulnerability Scanner — Sprint 25.5 (verification only, no exploits)."""

from __future__ import annotations

from typing import Any

from platform_enterprise_security_verification.models import VULN_CHECKS


class VulnerabilityScanner:
    def scan(self, *, findings: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        """Report verification results only — never generate exploit payloads."""
        findings = list(findings or [])
        results = []
        critical = 0
        for check in VULN_CHECKS:
            match = next((f for f in findings if f.get("check") == check), None)
            severity = (match or {}).get("severity", "none")
            passed = match is None or severity not in ("critical", "high")
            if severity == "critical":
                critical += 1
            results.append({
                "check": check,
                "passed": passed,
                "severity": severity,
                "verified_only": True,
                "exploit_payload": None,
            })
        return {
            "domain": "vulnerabilities",
            "checks": results,
            "critical_count": critical,
            "passed": critical == 0,
            "blocks_release": critical > 0,
        }
