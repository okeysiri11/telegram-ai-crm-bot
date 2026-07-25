"""Coverage Engine — Sprint 25.1."""

from __future__ import annotations

from typing import Any


class CoverageEngine:
    def measure(self, *, covered_lines: int, total_lines: int) -> dict[str, Any]:
        total_lines = max(int(total_lines), 1)
        covered_lines = max(0, min(int(covered_lines), total_lines))
        pct = round(covered_lines / total_lines, 3)
        return {
            "engine": "coverage",
            "covered_lines": covered_lines,
            "total_lines": total_lines,
            "coverage_pct": pct,
            "target_met": pct >= 0.7,
        }
