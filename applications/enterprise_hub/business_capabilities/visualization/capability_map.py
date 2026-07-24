
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

from applications.enterprise_hub.business_capabilities.capability_mapper import CapabilityMapper


class CapabilityMapViz:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.mapper = CapabilityMapper(self.store)

    def render(self, root_key: str = "enterprise") -> dict[str, Any]:
        hierarchy = self.mapper.hierarchy(root_key=root_key)
        vid = _id("ebc_vmap")
        record = {"viz_id": vid, "kind": "capability_map", "payload": hierarchy, "rendered_at": _now()}
        self.store.ebc_visualizations.save(vid, record)
        return record
