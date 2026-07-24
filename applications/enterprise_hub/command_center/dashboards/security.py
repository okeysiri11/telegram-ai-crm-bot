"""Security Dashboard — Sprint 20.12."""

from __future__ import annotations

from typing import Any


def blueprint() -> dict[str, Any]:
    return {
        "kind": "security",
        "title": "Security Dashboard",
        "sections": ['threats', 'incidents', 'access'],
        "default_widgets": ["kpi", "alerts", "ai_summary"],
    }
