"""Documentation Validator — Sprint 25.7."""

from __future__ import annotations

from typing import Any

from platform_enterprise_certification.models import DOCUMENTATION_ARTIFACTS


class DocumentationValidator:
    def validate(self, *, missing: list[str] | None = None) -> dict[str, Any]:
        missing = set(missing or [])
        artifacts = [
            {"artifact": name, "present": name not in missing, "passed": name not in missing}
            for name in DOCUMENTATION_ARTIFACTS
        ]
        passed = all(a["passed"] for a in artifacts)
        return {
            "artifacts": artifacts,
            "passed": passed,
            "missing": [a["artifact"] for a in artifacts if not a["passed"]],
            "blocks_release": not passed,
        }
