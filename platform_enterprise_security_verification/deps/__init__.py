"""Dependency Scanner — Sprint 25.5."""

from __future__ import annotations

from typing import Any

from platform_enterprise_security_verification.models import DEPENDENCY_SOURCES


class DependencyScanner:
    def scan(self, *, cves: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        cves = list(cves or [])
        critical = [c for c in cves if (c.get("severity") or "").lower() == "critical"]
        items = []
        for c in cves:
            items.append({
                "cve": c.get("cve", "UNKNOWN"),
                "package": c.get("package"),
                "source": c.get("source", "python_packages"),
                "severity": c.get("severity", "medium"),
                "available_fix": c.get("available_fix"),
                "risk_level": c.get("severity", "medium"),
            })
        return {
            "domain": "dependencies",
            "sources": list(DEPENDENCY_SOURCES),
            "findings": items,
            "critical_count": len(critical),
            "passed": len(critical) == 0,
            "blocks_release": len(critical) > 0,
        }
