"""Pattern Detection Engine — Sprint 24.8."""

from __future__ import annotations

from collections import Counter
from typing import Any


class PatternDetectionEngine:
    def detect(self, *, items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        items = list(items or [])
        types = Counter(i.get("kind", "unknown") for i in items)
        patterns = []
        for kind, count in types.most_common():
            if count >= 2:
                label = {
                    "error": "repeating_errors",
                    "request": "repeating_requests",
                    "best_practice": "best_practices",
                    "success": "successful_scenarios",
                    "profit": "high_profit_drivers",
                    "inefficiency": "low_efficiency_drivers",
                }.get(kind, "pattern")
                patterns.append({"pattern": label, "kind": kind, "count": count})
        if not patterns and items:
            patterns.append({"pattern": "insufficient_repetition", "count": len(items)})
        return {"patterns": patterns, "item_count": len(items)}
