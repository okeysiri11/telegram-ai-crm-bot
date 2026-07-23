"""DistributedExecution mode."""

from __future__ import annotations

from typing import Any


class DistributedExecution:
    name = "distributed"

    def describe(self) -> dict[str, Any]:
        return {"mode": self.name, "parallel": True, "order": "sharded"}
