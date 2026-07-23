"""RecursiveExecution mode."""

from __future__ import annotations

from typing import Any


class RecursiveExecution:
    name = "recursive"

    def describe(self) -> dict[str, Any]:
        return {"mode": self.name, "parallel": False, "order": "nested"}
