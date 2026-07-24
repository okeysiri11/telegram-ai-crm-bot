"""Manufacturing Dashboard — Sprint 20.12."""

from __future__ import annotations

from typing import Any


def blueprint() -> dict[str, Any]:
    return {
        "kind": "manufacturing",
        "title": "Manufacturing Dashboard",
        "sections": ['lines', 'oee', 'quality'],
        "default_widgets": ["kpi", "alerts", "ai_summary"],
    }
