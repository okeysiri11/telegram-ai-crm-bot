"""SequentialExecution mode."""

from __future__ import annotations

from typing import Any


class SequentialExecution:
    name = "sequential"

    def describe(self) -> dict[str, Any]:
        return {"mode": self.name, "parallel": False, "order": "strict"}
