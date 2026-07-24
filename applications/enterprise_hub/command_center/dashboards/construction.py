"""Construction Dashboard — Sprint 20.12."""

from __future__ import annotations

from typing import Any


def blueprint() -> dict[str, Any]:
    return {
        "kind": "construction",
        "title": "Construction Dashboard",
        "sections": ['sites', 'progress', 'safety'],
        "default_widgets": ["kpi", "alerts", "ai_summary"],
    }
