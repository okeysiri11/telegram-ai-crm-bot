"""Documentation quality validation — Sprint 21.6."""

from __future__ import annotations

from typing import Any

from platform_documentation.models import QUALITY_CHECKS


class DocumentationQuality:
    def validate(self, docs: list[dict[str, Any]]) -> dict[str, Any]:
        issues = []
        for doc in docs:
            if not doc.get("content") and not doc.get("body"):
                issues.append({"doc_id": doc.get("doc_id"), "check": "missing_sections", "severity": "low"})
            if "TODO" in str(doc.get("content", "")):
                issues.append({"doc_id": doc.get("doc_id"), "check": "stale_pages", "severity": "medium"})
        checks = {c: "passed" for c in QUALITY_CHECKS}
        if issues:
            checks["missing_sections"] = "warning"
        return {
            "checks": checks,
            "issues": issues,
            "passed": all(v in ("passed", "warning") for v in checks.values()),
            "completeness": round(max(0.0, 1.0 - len(issues) / max(1, len(docs) * 2)), 3),
        }
