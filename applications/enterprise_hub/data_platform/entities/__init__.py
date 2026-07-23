"""Master entity helpers."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.data_platform.models import ENTITY_TYPES
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def upsert_entity(
    store: EnterpriseHubStore,
    *,
    entity_type: str,
    name: str,
    attributes: dict[str, Any] | None = None,
    source: str = "edp",
    owner: str = "system",
) -> dict[str, Any]:
    et = entity_type.lower().strip()
    if et not in ENTITY_TYPES:
        raise ValidationError(f"entity_type must be one of {list(ENTITY_TYPES)}")
    if not name:
        raise ValidationError("name required")
    eid = _id("edp_ent")
    return store.edp_entities.save(
        eid,
        {
            "entity_id": eid,
            "entity_type": et,
            "name": name,
            "attributes": attributes or {},
            "source": source,
            "owner": owner,
            "version": 1,
            "status": "active",
            "at": _now(),
        },
    )
