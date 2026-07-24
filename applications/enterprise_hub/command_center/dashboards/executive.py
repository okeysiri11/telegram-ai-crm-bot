"""Executive Dashboard — Sprint 20.12."""

from __future__ import annotations

from typing import Any


def blueprint() -> dict[str, Any]:
    return {
        "kind": "executive",
        "title": "Executive Dashboard",
        "sections": ['company_state', 'kpi', 'cashflow', 'projects', 'load', 'ai_status', 'critical_events', 'forecasts'],
        "default_widgets": ["kpi", "alerts", "ai_summary"],
    }
