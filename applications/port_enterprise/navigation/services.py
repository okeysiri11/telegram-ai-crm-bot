"""Dashboards and knowledge for navigation suite."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.port_enterprise.shared.exceptions import ValidationError
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store

DASHBOARD_TYPES = ["vts", "ais", "radar", "navigation", "maritime_safety"]
REGISTRY_TYPES = ["navigation", "ais", "radar", "traffic", "safety"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class NavigationDashboard:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str = "vts") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "vts": {
                "centers": self.store.nav_vts_centers.count(),
                "traffic": self.store.nav_traffic.count(),
                "collision_watches": self.store.nav_collision.count(),
            },
            "ais": {
                "receivers": self.store.nav_ais_receivers.count(),
                "messages": self.store.nav_ais_messages.count(),
                "tracks": self.store.nav_ais_tracks.count(),
            },
            "radar": {
                "radars": self.store.nav_radars.count(),
                "targets": self.store.nav_radar_targets.count(),
                "alerts": self.store.nav_radar_alerts.count(),
            },
            "navigation": {
                "routes": self.store.nav_routes.count(),
                "fairways": self.store.nav_fairways.count(),
                "restrictions": self.store.nav_restrictions.count(),
            },
            "maritime_safety": {
                "risks": self.store.nav_safety_risks.count(),
                "warnings": self.store.nav_warnings.count(),
                "emergencies": self.store.nav_emergencies.count(),
            },
        }[dashboard_type]
        did = _id("nav_dash")
        return self.store.nav_dashboards.save(
            did,
            {"dashboard_id": did, "dashboard_type": dashboard_type, "metrics": metrics, "generated_at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.nav_dashboards.count(), "types": self.types}


class NavigationKnowledge:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store
        self.types = list(REGISTRY_TYPES)

    def publish(self, *, registry_type: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if registry_type not in self.types:
            raise ValidationError(f"registry_type must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("nav_reg")
        return self.store.nav_registries.save(
            rid,
            {
                "registry_id": rid,
                "registry_type": registry_type,
                "key": key,
                "payload": payload or {},
                "graph_node": f"nav:{registry_type}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.nav_registries.count(), "types": self.types}
