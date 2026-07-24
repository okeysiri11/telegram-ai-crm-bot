"""Command Center dashboard blueprints — Sprint 20.12."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.command_center.dashboards import (
    ai,
    construction,
    custom,
    executive,
    finance,
    healthcare,
    logistics,
    manufacturing,
    maritime,
    operations,
    security,
)

_MODULES = (
    executive,
    operations,
    finance,
    logistics,
    manufacturing,
    construction,
    maritime,
    healthcare,
    security,
    ai,
    custom,
)


def all_blueprints() -> list[dict[str, Any]]:
    return [m.blueprint() for m in _MODULES]
