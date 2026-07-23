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



from applications.enterprise_hub.data_fabric.models import SENSITIVITY


class MetadataManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def set_metadata(
        self,
        *,
        asset_id: str,
        owner: str = "data-ops",
        classification: str = "business",
        sensitivity: str = "internal",
        version: str = "1.0",
        related: list[str] | None = None,
        description: str = "",
    ) -> dict[str, Any]:
        if not asset_id:
            raise ValidationError("asset_id is required")
        if sensitivity not in SENSITIVITY:
            raise ValidationError(f"invalid sensitivity: {sensitivity}")
        mid = _id("edf_meta")
        return self.store.edf_metadata.save(
            mid,
            {
                "metadata_id": mid,
                "asset_id": asset_id,
                "owner": owner,
                "classification": classification,
                "sensitivity": sensitivity,
                "version": version,
                "related": list(related or []),
                "description": description,
                "updated_at": _now(),
            },
        )

    def for_asset(self, asset_id: str) -> list[dict[str, Any]]:
        return [m for m in self.store.edf_metadata.list_all() if m.get("asset_id") == asset_id]

    def status(self) -> dict[str, Any]:
        return {"metadata_records": len(self.store.edf_metadata.list_all())}
