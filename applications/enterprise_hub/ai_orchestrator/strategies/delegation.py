"""Delegation strategy."""

from __future__ import annotations

from typing import Any


class DelegationStrategy:
    name = "delegation"

    def describe(self) -> dict[str, Any]:
        return {"strategy": self.name, "parallel": False, "handoff": True}
