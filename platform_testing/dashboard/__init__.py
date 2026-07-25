"""Test Dashboard — Sprint 25.1."""

from __future__ import annotations

from typing import Any


class TestDashboard:
    def render(
        self,
        *,
        active: int = 0,
        passed: int = 0,
        failed: int = 0,
        skipped: int = 0,
        coverage_pct: float = 0.0,
        duration_ms: int = 0,
        history: list[dict[str, Any]] | None = None,
        reports: list[str] | None = None,
        trends: list[dict[str, Any]] | None = None,
        quality_score: float = 0.0,
    ) -> dict[str, Any]:
        return {
            "active_tests": int(active),
            "passed": int(passed),
            "failed": int(failed),
            "skipped": int(skipped),
            "coverage": float(coverage_pct),
            "duration_ms": int(duration_ms),
            "history": list(history or []),
            "reports": list(reports or []),
            "trends": list(trends or []),
            "quality_score": float(quality_score),
        }
