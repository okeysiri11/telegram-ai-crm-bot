"""Dashboards and knowledge for container management."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.port_enterprise.shared.exceptions import ValidationError
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store

DASHBOARD_TYPES = ["container", "yard", "equipment", "automation", "digital_twin"]
REGISTRY_TYPES = ["container", "equipment", "yard", "automation", "digital_twin"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class ContainerDashboard:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str = "container") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "container": {
                "containers": self.store.cm_containers.count(),
                "operations": self.store.cm_ops.count(),
            },
            "yard": {
                "yards": self.store.cm_yards.count(),
                "slots": self.store.cm_slots.count(),
            },
            "equipment": {
                "equipment": self.store.cm_equipment.count(),
                "maintenance": self.store.cm_eq_maint.count(),
            },
            "automation": {
                "tasks": self.store.cm_tasks.count(),
                "ai_opts": self.store.cm_ai_yard.count(),
            },
            "digital_twin": {
                "twins": self.store.cm_twins.count(),
                "simulations": self.store.cm_twin_sims.count(),
            },
        }[dashboard_type]
        did = _id("cm_dash")
        return self.store.cm_dashboards.save(
            did,
            {"dashboard_id": did, "dashboard_type": dashboard_type, "metrics": metrics, "generated_at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.cm_dashboards.count(), "types": self.types}


class ContainerKnowledge:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store
        self.types = list(REGISTRY_TYPES)

    def publish(self, *, registry_type: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if registry_type not in self.types:
            raise ValidationError(f"registry_type must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("cm_reg")
        return self.store.cm_registries.save(
            rid,
            {
                "registry_id": rid,
                "registry_type": registry_type,
                "key": key,
                "payload": payload or {},
                "graph_node": f"cm:{registry_type}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.cm_registries.count(), "types": self.types}
