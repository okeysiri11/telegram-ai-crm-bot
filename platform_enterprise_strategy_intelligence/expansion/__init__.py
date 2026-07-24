"""Expansion Planner — Sprint 24.7."""

from __future__ import annotations

from typing import Any


class ExpansionPlanner:
    DIMENSIONS = ("branches", "directions", "industries", "countries", "products")

    def plan(self, *, items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        items = list(items or [])
        by_dim: dict[str, list] = {d: [] for d in self.DIMENSIONS}
        for item in items:
            dim = (item.get("dimension") or "branches").lower()
            if dim not in by_dim:
                dim = "branches"
            by_dim[dim].append(item)
        return {
            "dimensions": list(self.DIMENSIONS),
            "plans": by_dim,
            "count": len(items),
        }
