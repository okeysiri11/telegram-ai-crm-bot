"""Command Center widgets — Sprint 20.12."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.command_center.widgets import (
    ai_summary,
    alerts,
    charts,
    kpi,
    maps,
    recommendations,
    timeline,
)

_MODULES = {
    "kpi": kpi,
    "charts": charts,
    "maps": maps,
    "timeline": timeline,
    "alerts": alerts,
    "ai_summary": ai_summary,
    "recommendations": recommendations,
}


def all_blueprints() -> list[dict[str, Any]]:
    return [m.blueprint() for m in _MODULES.values()]


def render_widget(kind: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    mod = _MODULES.get(kind)
    if not mod:
        raise KeyError(kind)
    return mod.render(payload)
