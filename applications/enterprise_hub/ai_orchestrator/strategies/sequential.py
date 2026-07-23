"""Sequential strategy."""

from __future__ import annotations

from typing import Any


class SequentialStrategy:
    name = "sequential"

    def describe(self) -> dict[str, Any]:
        return {"strategy": self.name, "parallel": False, "order": "strict"}
