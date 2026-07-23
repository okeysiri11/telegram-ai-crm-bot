"""Field mapper — source/target field pairing."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class FieldMapper:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def map_fields(
        self,
        *,
        source_fields: dict[str, Any],
        mapping: dict[str, str],
    ) -> dict[str, Any]:
        if not isinstance(source_fields, dict) or not isinstance(mapping, dict):
            raise ValidationError("source_fields and mapping required")
        result = {target: source_fields.get(src) for src, target in mapping.items()}
        mid = _id("eip_map")
        return self.store.eip_mappings.save(
            mid,
            {
                "mapping_id": mid,
                "mapping": mapping,
                "result": result,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"mappings": self.store.eip_mappings.count()}
