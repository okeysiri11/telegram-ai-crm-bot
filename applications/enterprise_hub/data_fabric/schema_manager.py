from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"




class SchemaManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def register(
        self,
        *,
        name: str,
        fields: list[dict[str, Any]] | None = None,
        version: str = "1.0",
        asset_id: str | None = None,
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("name is required")
        sid = _id("edf_sch")
        return self.store.edf_schemas.save(
            sid,
            {
                "schema_id": sid,
                "name": name,
                "version": version,
                "asset_id": asset_id,
                "fields": list(fields or [{"name": "id", "type": "string"}]),
                "registered_at": _now(),
            },
        )

    def validate(self, *, schema_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        schema = self.store.edf_schemas.get(schema_id)
        if not schema:
            raise NotFoundError(f"schema not found: {schema_id}")
        payload = payload or {}
        missing = [f["name"] for f in schema.get("fields") or [] if f.get("name") not in payload]
        return {"schema_id": schema_id, "valid": not missing, "missing": missing}

    def status(self) -> dict[str, Any]:
        return {"schemas": len(self.store.edf_schemas.list_all())}
