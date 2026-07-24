"""Alerts Widget — Sprint 20.12."""

from __future__ import annotations

from typing import Any


def blueprint() -> dict[str, Any]:
    return {"kind": "alerts", "title": "Alerts Widget", "fields": ['items', 'severity']}


def render(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = dict(payload or {})
    return {"kind": "alerts", "title": "Alerts Widget", "data": data}
