"""Collaborative strategy."""

from __future__ import annotations

from typing import Any


class CollaborativeStrategy:
    name = "collaborative"

    def describe(self) -> dict[str, Any]:
        return {"strategy": self.name, "parallel": True, "shared_context": True}
