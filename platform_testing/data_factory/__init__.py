"""Test Data Factory — Sprint 25.1."""

from __future__ import annotations

from typing import Any

from platform_testing.models import DATA_ENTITY_TYPES


class TestDataFactory:
    def generate(self, *, entity: str, count: int = 1) -> dict[str, Any]:
        entity = (entity or "").lower()
        if entity not in DATA_ENTITY_TYPES:
            raise ValueError(f"unsupported entity: {entity}")
        count = max(1, int(count))
        items = [{"id": f"{entity}_{i+1}", "entity": entity, "auto_generated": True} for i in range(count)]
        return {
            "entity": entity,
            "count": count,
            "items": items,
            "supported_entities": list(DATA_ENTITY_TYPES),
            "auto_generated": True,
        }
