"""Data catalog — discoverable inventory of platform data objects."""

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


class DataCatalog:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def publish(
        self,
        *,
        name: str,
        object_type: str,
        owner: str = "system",
        source: str = "edp",
        description: str = "",
        schema_ref: str = "",
        links: list[str] | None = None,
        version: str = "1.0",
    ) -> dict[str, Any]:
        if not name or not object_type:
            raise ValidationError("name and object_type required")
        cid = _id("edp_cat")
        return self.store.edp_catalog.save(
            cid,
            {
                "catalog_id": cid,
                "name": name,
                "object_type": object_type.lower(),
                "owner": owner,
                "source": source,
                "description": description,
                "schema": schema_ref,
                "links": links or [],
                "version": version,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.edp_catalog.count()}
