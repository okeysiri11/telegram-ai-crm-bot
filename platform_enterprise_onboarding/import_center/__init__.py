"""Data Import Center — Sprint 22.9."""

from __future__ import annotations

from typing import Any

from platform_enterprise_onboarding.models import IMPORT_ENTITIES, IMPORT_SOURCES


class DataImportCenter:
    def ingest(
        self,
        *,
        entity: str,
        source: str,
        rows: list[dict[str, Any]] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        entity = (entity or "").lower()
        source = (source or "").lower()
        if entity not in IMPORT_ENTITIES:
            raise ValueError(f"unsupported entity: {entity}")
        if source not in IMPORT_SOURCES:
            raise ValueError(f"unsupported source: {source}")
        rows = list(rows or [])
        if payload and isinstance(payload.get("rows"), list):
            rows = list(payload["rows"])
        return {
            "entity": entity,
            "source": source,
            "row_count": len(rows),
            "rows": rows,
            "status": "staged",
            "connector_ready": source != "future_connectors",
        }
