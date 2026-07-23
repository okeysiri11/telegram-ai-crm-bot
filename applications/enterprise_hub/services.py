"""Enterprise Hub dashboards and knowledge graph."""

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


class HubKnowledge:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.bases = list(DEFAULT_CONFIG.knowledge_bases)

    def publish(self, *, base: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if base not in self.bases:
            raise ValidationError(f"base must be one of {self.bases}")
        if not key:
            raise ValidationError("key required")
        eid = _id("hub_kg")
        return self.store.knowledge.save(
            eid,
            {
                "entry_id": eid,
                "base": base,
                "key": key,
                "payload": payload or {},
                "graph_node": f"hub:{base}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.knowledge.count(), "bases": self.bases}


class HubDashboard:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.types = list(DEFAULT_CONFIG.dashboard_types)

    def render(self, *, dashboard_type: str = "overview") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "overview": {
                "platforms": self.store.platforms.count(),
                "services": self.store.services.count(),
                "integrations": self.store.integrations.count(),
                "events": self.store.events.count(),
            },
            "platform_status": {
                "platforms": self.store.platforms.count(),
                "modules": self.store.modules.count(),
            },
            "integration_health": {
                "integrations": self.store.integrations.count(),
                "routes": self.store.routes.count(),
                "gateway_requests": self.store.gateway_requests.count(),
            },
            "connected_services": {
                "services": self.store.services.count(),
                "discoveries": self.store.discoveries.count(),
            },
            "environment_status": {
                "environments": self.store.environments.count(),
                "profiles": self.store.env_profiles.count(),
            },
        }[dashboard_type]
        did = _id("hub_dash")
        return self.store.dashboards.save(
            did,
            {
                "dashboard_id": did,
                "dashboard_type": dashboard_type,
                "metrics": metrics,
                "generated_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.dashboards.count(), "types": self.types}
