
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


class DeveloperApiGateway:
    """Gateway for plugin-facing developer APIs."""

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def route(
        self,
        *,
        path: str,
        method: str = "GET",
        plugin_id: str = "system",
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not path:
            raise ValidationError("path is required")
        rid = _id("sdp_gw")
        record = {
            "route_id": rid,
            "path": path,
            "method": method.upper(),
            "plugin_id": plugin_id,
            "payload": payload or {},
            "status": 200,
            "at": _now(),
        }
        return self.store.sdp_gateway.save(rid, record)

    def status(self) -> dict[str, Any]:
        return {"routes": len(self.store.sdp_gateway.list_all())}
