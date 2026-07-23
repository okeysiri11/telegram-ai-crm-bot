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



from applications.enterprise_hub.data_fabric.models import VIRTUALIZATION_MODES


class DataVirtualization:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def create_view(
        self,
        *,
        name: str,
        mode: str,
        sources: list[str] | None = None,
        projection: list[str] | None = None,
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("name is required")
        if mode not in VIRTUALIZATION_MODES:
            raise ValidationError(f"invalid mode: {mode}")
        vid = _id("edf_view")
        return self.store.edf_views.save(
            vid,
            {
                "view_id": vid,
                "name": name,
                "mode": mode,
                "sources": list(sources or []),
                "projection": list(projection or ["*"]),
                "physical_move": False,
                "created_at": _now(),
            },
        )

    def query_view(self, *, view_id: str, predicate: str = "") -> dict[str, Any]:
        view = self.store.edf_views.get(view_id)
        if not view:
            raise NotFoundError(f"view not found: {view_id}")
        qid = _id("edf_vq")
        rows = [{"source": s, "value": f"{s}:{predicate or 'all'}"} for s in view.get("sources") or ["virtual"]]
        return self.store.edf_virtual_queries.save(
            qid,
            {
                "query_id": qid,
                "view_id": view_id,
                "mode": view.get("mode"),
                "predicate": predicate,
                "rows": rows,
                "row_count": len(rows),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "views": len(self.store.edf_views.list_all()),
            "queries": len(self.store.edf_virtual_queries.list_all()),
        }
