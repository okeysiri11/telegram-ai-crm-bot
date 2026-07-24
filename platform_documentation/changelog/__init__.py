"""Changelog — Sprint 21.6."""

from __future__ import annotations

from typing import Any


class Changelog:
    def entries(self, *, version: str) -> list[dict[str, Any]]:
        return [
            {"version": version, "type": "feature", "summary": "Enterprise Documentation Platform"},
            {"version": version, "type": "docs", "summary": "Auto-generated architecture and API docs"},
        ]
