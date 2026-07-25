"""Regression Engine — Sprint 25.1."""

from __future__ import annotations

from typing import Any


class RegressionEngine:
    def run(self, *, baseline_pass_rate: float = 1.0, current_pass_rate: float = 1.0) -> dict[str, Any]:
        ok = float(current_pass_rate) >= float(baseline_pass_rate) - 0.01
        return {
            "engine": "regression",
            "baseline_pass_rate": float(baseline_pass_rate),
            "current_pass_rate": float(current_pass_rate),
            "passed": ok,
            "regressions": [] if ok else ["pass_rate_drop"],
        }
