"""Logistics Dashboard — Sprint 20.12."""

from __future__ import annotations

from typing import Any


def blueprint() -> dict[str, Any]:
    return {
        "kind": "logistics",
        "title": "Logistics Dashboard",
        "sections": ['fleet', 'dispatch', 'routes'],
        "default_widgets": ["kpi", "alerts", "ai_summary"],
    }
