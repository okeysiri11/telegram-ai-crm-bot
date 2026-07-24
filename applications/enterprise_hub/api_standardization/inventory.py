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

from applications.enterprise_hub.api_standardization.models import API_CATEGORIES, KNOWN_HUB_ENDPOINTS


class ApiInventory:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def scan(self) -> dict[str, Any]:
        items = []
        for path, category, service in KNOWN_HUB_ENDPOINTS:
            eid = _id("eas_ep")
            item = {
                "endpoint_id": eid,
                "path": path,
                "category": category,
                "service": service,
                "inventoried_at": _now(),
            }
            self.store.eas_endpoints.save(eid, item)
            items.append(item)
        iid = _id("eas_inv")
        by_cat = {c: sum(1 for i in items if i["category"] == c) for c in API_CATEGORIES}
        record = {
            "inventory_id": iid,
            "total": len(items),
            "by_category": by_cat,
            "scanned_at": _now(),
        }
        self.store.eas_inventories.save(iid, record)
        return {**record, "items": items}

    def list_endpoints(self) -> list[dict[str, Any]]:
        return self.store.eas_endpoints.list_all()

    def status(self) -> dict[str, Any]:
        return {
            "endpoints": len(self.store.eas_endpoints.list_all()),
            "inventories": len(self.store.eas_inventories.list_all()),
        }
