"""Dashboards and knowledge for multimodal logistics."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.port_enterprise.shared.exceptions import ValidationError
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store

DASHBOARD_TYPES = ["rail", "truck", "multimodal", "shipment", "ai_logistics"]
REGISTRY_TYPES = ["logistics", "rail", "truck", "shipment", "multimodal"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class MultimodalDashboard:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str = "multimodal") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "rail": {
                "trains": self.store.ml_trains.count(),
                "schedules": self.store.ml_rail_schedules.count(),
            },
            "truck": {
                "trucks": self.store.ml_trucks.count(),
                "dispatches": self.store.ml_truck_dispatch.count(),
            },
            "multimodal": {
                "chains": self.store.ml_chains.count(),
                "transfers": self.store.ml_transfers.count(),
            },
            "shipment": {
                "shipments": self.store.ml_shipments.count(),
                "pods": self.store.ml_pods.count(),
            },
            "ai_logistics": {
                "demand": self.store.ml_ai_demand.count(),
                "routes": self.store.ml_ai_routes.count(),
                "carbon": self.store.ml_ai_carbon.count(),
            },
        }[dashboard_type]
        did = _id("ml_dash")
        return self.store.ml_dashboards.save(
            did,
            {"dashboard_id": did, "dashboard_type": dashboard_type, "metrics": metrics, "generated_at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.ml_dashboards.count(), "types": self.types}


class MultimodalKnowledge:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store
        self.types = list(REGISTRY_TYPES)

    def publish(self, *, registry_type: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if registry_type not in self.types:
            raise ValidationError(f"registry_type must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("ml_reg")
        return self.store.ml_registries.save(
            rid,
            {
                "registry_id": rid,
                "registry_type": registry_type,
                "key": key,
                "payload": payload or {},
                "graph_node": f"ml:{registry_type}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.ml_registries.count(), "types": self.types}
