"""Parallel strategy."""

from __future__ import annotations

from typing import Any


class ParallelStrategy:
    name = "parallel"

    def describe(self) -> dict[str, Any]:
        return {"strategy": self.name, "parallel": True, "order": "any"}
