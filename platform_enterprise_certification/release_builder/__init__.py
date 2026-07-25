"""Release Builder — Sprint 25.7."""

from __future__ import annotations

from typing import Any

from platform_enterprise_certification.models import RELEASE_ARTIFACTS


class ReleaseBuilder:
    def build(self, *, version: str, build_number: str) -> dict[str, Any]:
        if not version:
            raise ValueError("version is required")
        artifacts = [
            {
                "artifact": name,
                "path": f"dist/{version}/{name}",
                "built": True,
            }
            for name in RELEASE_ARTIFACTS
        ]
        return {
            "version": version,
            "build_number": build_number,
            "artifacts": artifacts,
            "package_ready": True,
            "passed": True,
        }
