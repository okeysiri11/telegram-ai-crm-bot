"""Charts Widget — Sprint 20.12."""

from __future__ import annotations

from typing import Any


def blueprint() -> dict[str, Any]:
    return {"kind": "charts", "title": "Charts Widget", "fields": ['series', 'period']}


def render(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = dict(payload or {})
    return {"kind": "charts", "title": "Charts Widget", "data": data}
