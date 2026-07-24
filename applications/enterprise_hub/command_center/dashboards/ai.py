"""AI Dashboard — Sprint 20.12."""

from __future__ import annotations

from typing import Any


def blueprint() -> dict[str, Any]:
    return {
        "kind": "ai",
        "title": "AI Dashboard",
        "sections": ['agents', 'orchestration', 'coverage'],
        "default_widgets": ["kpi", "alerts", "ai_summary"],
    }
