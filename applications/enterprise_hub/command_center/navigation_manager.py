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

from applications.enterprise_hub.command_center.models import DASHBOARD_KINDS


class NavigationManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def tree(self) -> dict[str, Any]:
        nid = _id("ecc_nav")
        record = {
            "navigation_id": nid,
            "sections": [
                {"id": "home", "label": "Command Center", "children": ["executive", "operations"]},
                {"id": "domains", "label": "Domains", "children": list(DASHBOARD_KINDS)},
                {"id": "control", "label": "Control", "children": ["alerts", "actions", "situation_room", "map"]},
            ],
            "built_at": _now(),
        }
        self.store.ecc_navigation.save(nid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {"navigation": len(self.store.ecc_navigation.list_all())}
