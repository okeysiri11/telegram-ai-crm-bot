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




class FederationEngine:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def federate(
        self,
        *,
        sources: list[str] | None = None,
        query: str = "",
        join_key: str = "entity_id",
    ) -> dict[str, Any]:
        srcs = list(sources or [])
        if len(srcs) < 2:
            raise ValidationError("federation requires at least 2 sources")
        fid = _id("edf_fed")
        partials = []
        for s in srcs:
            partials.append({"source": s, "rows": [{"entity_id": "E1", "source": s, "payload": query or s}]})
        merged = {"entity_id": "E1", "parts": {p["source"]: p["rows"][0] for p in partials}}
        return self.store.edf_federations.save(
            fid,
            {
                "federation_id": fid,
                "sources": srcs,
                "query": query,
                "join_key": join_key,
                "partials": partials,
                "result": merged,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"federations": len(self.store.edf_federations.list_all())}
