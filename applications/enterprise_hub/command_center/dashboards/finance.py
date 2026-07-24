"""Finance Dashboard — Sprint 20.12."""

from __future__ import annotations

from typing import Any


def blueprint() -> dict[str, Any]:
    return {
        "kind": "finance",
        "title": "Finance Dashboard",
        "sections": ['cashflow', 'revenue', 'costs', 'risk'],
        "default_widgets": ["kpi", "alerts", "ai_summary"],
    }
