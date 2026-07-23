
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

from applications.enterprise_hub.developer_platform.models import EXTENSION_POINTS


class ExtensionManager:
    """Register extension points (menu, UI, agents, workflow, reports, etc.)."""

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def extend(
        self,
        *,
        plugin_id: str,
        point: str,
        label: str,
        handler: str = "default",
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if point not in EXTENSION_POINTS:
            raise ValidationError(f"invalid extension point: {point}")
        if not plugin_id or not label:
            raise ValidationError("plugin_id and label are required")
        eid = _id("sdp_ext")
        record = {
            "extension_id": eid,
            "plugin_id": plugin_id,
            "point": point,
            "label": label,
            "handler": handler,
            "payload": payload or {},
            "created_at": _now(),
        }
        return self.store.sdp_extensions.save(eid, record)

    def list_for(self, plugin_id: str | None = None, point: str | None = None) -> list[dict[str, Any]]:
        items = self.store.sdp_extensions.list_all()
        if plugin_id:
            items = [i for i in items if i.get("plugin_id") == plugin_id]
        if point:
            items = [i for i in items if i.get("point") == point]
        return items

    def status(self) -> dict[str, Any]:
        items = self.store.sdp_extensions.list_all()
        by_point: dict[str, int] = {}
        for i in items:
            p = i.get("point", "?")
            by_point[p] = by_point.get(p, 0) + 1
        return {"extensions": len(items), "by_point": by_point, "points": list(EXTENSION_POINTS)}
