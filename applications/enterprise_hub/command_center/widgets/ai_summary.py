"""AI Summary Widget — Sprint 20.12."""

from __future__ import annotations

from typing import Any


def blueprint() -> dict[str, Any]:
    return {"kind": "ai_summary", "title": "AI Summary Widget", "fields": ['summary', 'highlights']}


def render(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = dict(payload or {})
    return {"kind": "ai_summary", "title": "AI Summary Widget", "data": data}
