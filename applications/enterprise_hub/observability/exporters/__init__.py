"""Telemetry exporters."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.observability.models import EXPORTERS
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def export_telemetry(
    store: EnterpriseHubStore,
    *,
    exporter: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    e = exporter.lower().strip()
    if e not in EXPORTERS:
        raise ValidationError(f"exporter must be one of {list(EXPORTERS)}")
    eid = _id("obs_exp")
    return store.obs_exports.save(
        eid,
        {
            "export_id": eid,
            "exporter": e,
            "payload": payload or {},
            "status": "ok",
            "at": _now(),
        },
    )
