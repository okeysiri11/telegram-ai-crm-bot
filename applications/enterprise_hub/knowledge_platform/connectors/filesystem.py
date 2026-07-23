"""FilesystemConnector — ingest source connector."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class FilesystemConnector:
    kind = "filesystem"

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def sync(self, *, path: str, meta: dict[str, Any] | None = None) -> dict[str, Any]:
        cid = _id("ekp_conn")
        return self.store.ekp_connectors.save(
            cid,
            {
                "connector_id": cid,
                "kind": self.kind,
                "path": path,
                "meta": meta or {},
                "status": "synced",
                "at": _now(),
            },
        )
