"""Integration layer — unified API, ESB, discovery, gateway, routing, aggregation."""

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


class IntegrationLayer:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def discover(self, *, service_name: str, platform: str = "") -> dict[str, Any]:
        if not service_name:
            raise ValidationError("service_name required")
        matches = [
            s
            for s in self.store.services.list_all()
            if s["name"] == service_name and (not platform or s["platform"] == platform.lower())
        ]
        did = _id("hub_disc")
        return self.store.discoveries.save(
            did,
            {
                "discovery_id": did,
                "service_name": service_name,
                "platform": platform.lower(),
                "matches": len(matches),
                "services": matches,
                "at": _now(),
            },
        )

    def route_request(
        self, *, path: str, method: str = "GET", target_platform: str = ""
    ) -> dict[str, Any]:
        if not path:
            raise ValidationError("path required")
        rid = _id("hub_route")
        return self.store.routes.save(
            rid,
            {
                "route_id": rid,
                "path": path,
                "method": method.upper(),
                "target_platform": target_platform.lower(),
                "status": "routed",
                "at": _now(),
            },
        )

    def gateway(
        self,
        *,
        path: str,
        method: str = "GET",
        payload: dict[str, Any] | None = None,
        target_platform: str = "",
    ) -> dict[str, Any]:
        route = self.route_request(path=path, method=method, target_platform=target_platform)
        gid = _id("hub_gw")
        return self.store.gateway_requests.save(
            gid,
            {
                "gateway_id": gid,
                "route_id": route["route_id"],
                "path": path,
                "method": method.upper(),
                "target_platform": target_platform.lower(),
                "payload": payload or {},
                "status": "accepted",
                "at": _now(),
            },
        )

    def aggregate(self, *, label: str, responses: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        if not label:
            raise ValidationError("label required")
        aid = _id("hub_agg")
        items = responses or []
        return self.store.aggregations.save(
            aid,
            {
                "aggregation_id": aid,
                "label": label,
                "count": len(items),
                "responses": items,
                "at": _now(),
            },
        )

    def publish_bus(
        self, *, topic: str, message: dict[str, Any] | None = None, source: str = "hub"
    ) -> dict[str, Any]:
        if not topic:
            raise ValidationError("topic required")
        mid = _id("hub_bus")
        return self.store.bus_messages.save(
            mid,
            {
                "message_id": mid,
                "topic": topic,
                "source": source,
                "message": message or {},
                "status": "published",
                "at": _now(),
            },
        )

    def get_route(self, route_id: str) -> dict[str, Any]:
        route = self.store.routes.get(route_id)
        if route is None:
            raise NotFoundError(f"route not found: {route_id}")
        return route

    def status(self) -> dict[str, Any]:
        return {
            "discoveries": self.store.discoveries.count(),
            "routes": self.store.routes.count(),
            "gateway_requests": self.store.gateway_requests.count(),
            "aggregations": self.store.aggregations.count(),
            "bus_messages": self.store.bus_messages.count(),
        }
