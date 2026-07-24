"""Maritime Dashboard — Sprint 20.12."""

from __future__ import annotations

from typing import Any


def blueprint() -> dict[str, Any]:
    return {
        "kind": "maritime",
        "title": "Maritime Dashboard",
        "sections": ['vessels', 'berths', 'cargo'],
        "default_widgets": ["kpi", "alerts", "ai_summary"],
    }
