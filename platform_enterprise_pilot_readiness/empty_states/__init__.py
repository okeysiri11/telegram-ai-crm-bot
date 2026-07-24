"""Empty State Designer — Sprint 23.1."""

from __future__ import annotations

from typing import Any


class EmptyStateDesigner:
    def design(self, *, screen: str) -> dict[str, Any]:
        if not screen:
            raise ValueError("screen is required")
        return {
            "screen": screen,
            "empty_state": f"No {screen} yet",
            "hint": f"Create your first {screen} to get started",
            "training_message": f"Tip: use Quick Start to seed sample {screen}",
            "sample_data": [{"id": "sample_1", "label": f"Sample {screen}"}],
            "quick_start": True,
        }
