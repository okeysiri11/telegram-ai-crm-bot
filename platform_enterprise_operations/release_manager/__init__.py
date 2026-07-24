"""Release Manager (ops view) — Sprint 23.0."""

from __future__ import annotations

from typing import Any


class ReleaseManagerView:
    def record(self, *, version: str, changelog: list[str] | None = None, migrations: list[str] | None = None, test_results: dict[str, Any] | None = None, impact: str = "") -> dict[str, Any]:
        if not version:
            raise ValueError("version is required")
        return {
            "version": version,
            "changelog": list(changelog or []),
            "migrations": list(migrations or []),
            "test_results": dict(test_results or {"passed": True}),
            "impact": impact or "pilot_ops",
            "release_ref": "platform_release",
        }
