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



from applications.enterprise_hub.data_fabric.models import ASSET_KINDS, SOURCE_TYPES


class DataCatalog:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def register(
        self,
        *,
        name: str,
        kind: str,
        source: str = "custom",
        owner: str = "data-ops",
        description: str = "",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("name is required")
        if kind not in ASSET_KINDS:
            raise ValidationError(f"invalid asset kind: {kind}")
        if source not in SOURCE_TYPES:
            raise ValidationError(f"invalid source: {source}")
        aid = _id("edf_asset")
        return self.store.edf_assets.save(
            aid,
            {
                "asset_id": aid,
                "name": name,
                "kind": kind,
                "source": source,
                "owner": owner,
                "description": description or name,
                "tags": list(tags or []),
                "registered_at": _now(),
                "status": "active",
            },
        )

    def get(self, asset_id: str) -> dict[str, Any]:
        item = self.store.edf_assets.get(asset_id)
        if not item:
            raise NotFoundError(f"asset not found: {asset_id}")
        return item

    def search(self, *, query: str = "", kind: str | None = None, source: str | None = None) -> list[dict[str, Any]]:
        items = self.store.edf_assets.list_all()
        q = query.lower().strip()
        out = []
        for i in items:
            if q and q not in i.get("name", "").lower() and q not in i.get("description", "").lower():
                continue
            if kind and i.get("kind") != kind:
                continue
            if source and i.get("source") != source:
                continue
            out.append(i)
        return out

    def status(self) -> dict[str, Any]:
        items = self.store.edf_assets.list_all()
        by_kind: dict[str, int] = {}
        for i in items:
            k = i.get("kind", "?")
            by_kind[k] = by_kind.get(k, 0) + 1
        return {"assets": len(items), "by_kind": by_kind}
