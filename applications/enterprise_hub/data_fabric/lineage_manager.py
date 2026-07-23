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




class LineageManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def record(
        self,
        *,
        asset_id: str,
        upstream: list[str] | None = None,
        transforms: list[str] | None = None,
        consumers: list[str] | None = None,
    ) -> dict[str, Any]:
        if not asset_id:
            raise ValidationError("asset_id is required")
        lid = _id("edf_lin")
        return self.store.edf_lineage.save(
            lid,
            {
                "lineage_id": lid,
                "asset_id": asset_id,
                "upstream": list(upstream or []),
                "transforms": list(transforms or []),
                "consumers": list(consumers or []),
                "recorded_at": _now(),
            },
        )

    def for_asset(self, asset_id: str) -> list[dict[str, Any]]:
        return [l for l in self.store.edf_lineage.list_all() if l.get("asset_id") == asset_id]

    def status(self) -> dict[str, Any]:
        return {"lineage_records": len(self.store.edf_lineage.list_all())}
