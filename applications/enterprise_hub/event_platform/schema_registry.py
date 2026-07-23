"""Schema registry — event payload schemas and compatibility."""

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


class SchemaRegistry:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def register(
        self,
        *,
        event_type: str,
        version: str,
        fields: list[str] | None = None,
        compatible_with: list[str] | None = None,
    ) -> dict[str, Any]:
        if not event_type or not version:
            raise ValidationError("event_type and version required")
        sid = _id("evp_sch")
        return self.store.evp_schemas.save(
            sid,
            {
                "schema_id": sid,
                "event_type": event_type,
                "version": version,
                "fields": fields or ["id", "timestamp"],
                "compatible_with": compatible_with or [],
                "at": _now(),
            },
        )

    def validate_payload(self, *, schema_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        schema = self.store.evp_schemas.get(schema_id)
        if not schema:
            raise NotFoundError(f"schema not found: {schema_id}")
        missing = [f for f in (schema.get("fields") or []) if f not in (payload or {})]
        return {
            "schema_id": schema_id,
            "valid": not missing,
            "missing": missing,
        }

    def status(self) -> dict[str, Any]:
        return {"schemas": self.store.evp_schemas.count()}
