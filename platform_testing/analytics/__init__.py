"""Test Analytics — Sprint 25.1."""

from __future__ import annotations

from typing import Any


class TestAnalytics:
    def analyze(self, *, runs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        runs = list(runs or [])
        durations = [float(r.get("duration_ms", 0)) for r in runs]
        failures = sum(int(r.get("failed", 0)) for r in runs)
        flaky = [r.get("run_id") for r in runs if r.get("flaky")]
        by_module: dict[str, dict[str, int]] = {}
        for r in runs:
            for m, stats in (r.get("by_module") or {}).items():
                slot = by_module.setdefault(m, {"passed": 0, "failed": 0})
                slot["passed"] += int(stats.get("passed", 0))
                slot["failed"] += int(stats.get("failed", 0))
        avg = round(sum(durations) / len(durations), 2) if durations else 0.0
        return {
            "avg_duration_ms": avg,
            "error_count": failures,
            "flaky_tests": flaky,
            "error_repeatability": round(len(flaky) / max(len(runs), 1), 3),
            "success_by_module": by_module,
            "run_history": [{"run_id": r.get("run_id"), "success": r.get("success")} for r in runs],
        }
