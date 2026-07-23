"""Voting strategy."""

from __future__ import annotations

from typing import Any


class VotingStrategy:
    name = "voting"

    def describe(self) -> dict[str, Any]:
        return {"strategy": self.name, "parallel": True, "resolve": "majority"}
