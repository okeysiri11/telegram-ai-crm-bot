"""Contract documentation generator — Sprint 21.3."""

from __future__ import annotations

from typing import Any

from platform_contracts.models import DOMAINS, EVENT_REQUIRED_FIELDS, BASE_DTO_FIELDS
from platform_contracts.registry import DtoRegistry, SchemaRegistry


class DocumentationGenerator:
    def generate(self, *, dto_registry: DtoRegistry, schema_registry: SchemaRegistry) -> dict[str, Any]:
        dtos = dto_registry.list_all()
        return {
            "title": "Enterprise Data Contracts",
            "base_dto_fields": list(BASE_DTO_FIELDS),
            "event_fields": list(EVENT_REQUIRED_FIELDS),
            "domains": list(DOMAINS),
            "dto_catalog": dtos,
            "schema_status": schema_registry.status(),
            "examples": {
                "dto": {"id": "dto_example", "version": 1, "metadata": {}},
                "event": {
                    "event_id": "evt_example",
                    "event_type": "domain.entity.created",
                    "aggregate_id": "agg_1",
                    "aggregate_type": "contact",
                    "source_service": "crm",
                    "actor": "user",
                    "payload": {},
                    "schema_version": 1,
                    "timestamp": "2026-07-24T00:00:00+00:00",
                    "trace_id": "trace_1",
                },
            },
            "dependencies": [
                {"from": "BaseDTO", "to": d} for d in ("crm", "erp", "ai", "workflow")
            ],
        }
