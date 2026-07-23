"""ParallelExecution mode."""

from __future__ import annotations

from typing import Any


class ParallelExecution:
    name = "parallel"

    def describe(self) -> dict[str, Any]:
        return {"mode": self.name, "parallel": True, "order": "any"}
