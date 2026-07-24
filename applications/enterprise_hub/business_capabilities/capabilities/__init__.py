"""Capability domain seed modules — Sprint 20.11."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.business_capabilities.capabilities import (
    ai_operations,
    construction,
    crm,
    custom,
    finance,
    healthcare,
    hr,
    legal,
    logistics,
    manufacturing,
    maritime,
    procurement,
    sales,
    warehouse,
)

_MODULES = (
    finance,
    sales,
    crm,
    procurement,
    logistics,
    warehouse,
    manufacturing,
    construction,
    maritime,
    healthcare,
    legal,
    hr,
    ai_operations,
    custom,
)


def all_definitions() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for mod in _MODULES:
        for item in mod.definitions():
            key = item["key"]
            if key in seen:
                continue
            seen.add(key)
            items.append(item)
    return items


DEFAULT_DEPENDENCIES = [
    ("sales", "crm"),
    ("crm", "warehouse"),
    ("warehouse", "procurement"),
    ("procurement", "manufacturing"),
    ("manufacturing", "logistics"),
    ("logistics", "finance"),
    ("maritime", "logistics"),
    ("maritime.customs", "legal.compliance"),
    ("ai_operations", "crm"),
]
