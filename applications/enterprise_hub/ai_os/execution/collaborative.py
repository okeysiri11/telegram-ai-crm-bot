"""CollaborativeExecution mode."""

from __future__ import annotations

from typing import Any


class CollaborativeExecution:
    name = "collaborative"

    def describe(self) -> dict[str, Any]:
        return {"mode": self.name, "parallel": True, "order": "shared"}
