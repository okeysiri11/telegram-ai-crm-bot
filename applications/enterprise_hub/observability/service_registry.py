"""Service registry — microservices, AI agents, integrations, queues, jobs."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.observability.models import SERVICE_KINDS
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ServiceRegistry:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def register(
        self,
        *,
        name: str,
        kind: str,
        version: str = "1.0",
        owners: list[str] | None = None,
        dependencies: list[str] | None = None,
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("name required")
        k = kind.lower().strip()
        if k not in SERVICE_KINDS:
            raise ValidationError(f"kind must be one of {list(SERVICE_KINDS)}")
        sid = _id("obs_svc")
        return self.store.obs_services.save(
            sid,
            {
                "service_id": sid,
                "name": name,
                "kind": k,
                "version": version,
                "owners": owners or ["ops"],
                "dependencies": dependencies or [],
                "status": "registered",
                "health_status": "unknown",
                "at": _now(),
            },
        )

    def set_health(self, *, service_id: str, health_status: str) -> dict[str, Any]:
        svc = self.store.obs_services.get(service_id)
        if svc is None:
            raise NotFoundError(f"service not found: {service_id}")
        svc["health_status"] = health_status
        svc["status"] = "running" if health_status == "healthy" else svc.get("status", "registered")
        svc["at"] = _now()
        return self.store.obs_services.save(service_id, svc)

    def status(self) -> dict[str, Any]:
        return {"services": self.store.obs_services.count(), "kinds": list(SERVICE_KINDS)}
