"""Healthcare Dashboard — Sprint 20.12."""

from __future__ import annotations

from typing import Any


def blueprint() -> dict[str, Any]:
    return {
        "kind": "healthcare",
        "title": "Healthcare Dashboard",
        "sections": ['facilities', 'capacity', 'care'],
        "default_widgets": ["kpi", "alerts", "ai_summary"],
    }
