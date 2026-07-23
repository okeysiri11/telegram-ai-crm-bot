"""Metric collectors."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.observability.models import COLLECTORS
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def collect(
    store: EnterpriseHubStore,
    *,
    collector: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    c = collector.lower().strip()
    if c not in COLLECTORS:
        raise ValidationError(f"collector must be one of {list(COLLECTORS)}")
    cid = _id("obs_col")
    return store.obs_collections.save(
        cid,
        {
            "collection_id": cid,
            "collector": c,
            "payload": payload or {},
            "at": _now(),
        },
    )
