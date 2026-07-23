"""Cross-platform routing — automotive, agro, port, crypto, legal, finance, multi."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CrossPlatformRouting:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.platforms = list(DEFAULT_CONFIG.orch_route_platforms)

    def route(
        self,
        *,
        platform: str,
        action: str,
        payload: dict[str, Any] | None = None,
        workflow_ref: str = "",
    ) -> dict[str, Any]:
        plat = platform.lower().strip()
        if plat not in self.platforms:
            raise ValidationError(f"platform must be one of {self.platforms}")
        if not action:
            raise ValidationError("action required")
        rid = _id("orch_rt")
        return self.store.orch_routes.save(
            rid,
            {
                "route_id": rid,
                "platform": plat,
                "action": action,
                "payload": payload or {},
                "workflow_ref": workflow_ref,
                "status": "routed",
                "at": _now(),
            },
        )

    def coordinate(
        self, *, platforms: list[str], action: str, label: str = ""
    ) -> dict[str, Any]:
        if not platforms or not action:
            raise ValidationError("platforms and action required")
        for p in platforms:
            if p.lower() not in self.platforms:
                raise ValidationError(f"platform must be one of {self.platforms}")
        cid = _id("orch_coord")
        route_ids = [
            self.route(platform=p, action=action, workflow_ref=cid)["route_id"] for p in platforms
        ]
        return self.store.orch_coordinations.save(
            cid,
            {
                "coordination_id": cid,
                "platforms": [p.lower() for p in platforms],
                "action": action,
                "label": label or action,
                "route_ids": route_ids,
                "status": "coordinated",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "routes": self.store.orch_routes.count(),
            "coordinations": self.store.orch_coordinations.count(),
            "platforms": self.platforms,
        }
