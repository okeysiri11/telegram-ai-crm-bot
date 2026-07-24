"""KPI Widget — Sprint 20.12."""

from __future__ import annotations

from typing import Any


def blueprint() -> dict[str, Any]:
    return {"kind": "kpi", "title": "KPI Widget", "fields": ['value', 'target', 'trend']}


def render(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = dict(payload or {})
    return {"kind": "kpi", "title": "KPI Widget", "data": data}
