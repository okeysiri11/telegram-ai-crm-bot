"""Custom Dashboard — Sprint 20.12."""

from __future__ import annotations

from typing import Any


def blueprint() -> dict[str, Any]:
    return {
        "kind": "custom",
        "title": "Custom Dashboard",
        "sections": ['widgets'],
        "default_widgets": ["kpi", "alerts", "ai_summary"],
    }
