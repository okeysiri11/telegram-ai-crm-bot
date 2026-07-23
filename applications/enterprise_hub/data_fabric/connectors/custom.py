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


class CustomConnector:
    KIND = "custom"

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def connect(self, *, name: str, endpoint: str = "local", status: str = "connected") -> dict[str, Any]:
        if not name:
            raise ValidationError("name is required")
        cid = _id("edf_conn")
        return self.store.edf_connectors.save(
            cid,
            {
                "connector_id": cid,
                "kind": self.KIND,
                "name": name,
                "endpoint": endpoint,
                "status": status,
                "connected_at": _now(),
            },
        )

    def query(self, *, connector_id: str, query: str, limit: int = 10) -> dict[str, Any]:
        conn = self.store.edf_connectors.get(connector_id)
        if not conn:
            raise NotFoundError(f"connector not found: {connector_id}")
        qid = _id("edf_cq")
        rows = [{"id": i, "source": self.KIND, "value": f"row-{i}"} for i in range(min(limit, 5))]
        return self.store.edf_connector_queries.save(
            qid,
            {
                "query_id": qid,
                "connector_id": connector_id,
                "kind": self.KIND,
                "query": query,
                "rows": rows,
                "row_count": len(rows),
                "latency_ms": 5 + len(query) % 20,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        items = [c for c in self.store.edf_connectors.list_all() if c.get("kind") == self.KIND]
        return {"kind": self.KIND, "connectors": len(items)}
