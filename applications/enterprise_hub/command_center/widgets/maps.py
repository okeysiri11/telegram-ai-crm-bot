"""Maps Widget — Sprint 20.12."""

from __future__ import annotations

from typing import Any


def blueprint() -> dict[str, Any]:
    return {"kind": "maps", "title": "Maps Widget", "fields": ['entities', 'layers']}


def render(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = dict(payload or {})
    return {"kind": "maps", "title": "Maps Widget", "data": data}
