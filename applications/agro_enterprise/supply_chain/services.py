"""Dashboards and knowledge for agro supply chain."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.agro_enterprise.shared.exceptions import ValidationError
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store

DASHBOARD_TYPES = ["supply_chain", "warehouse", "elevator", "export", "trading", "logistics"]
REGISTRY_TYPES = ["supply_chain", "warehouse", "elevator", "quality", "export"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class SupplyChainDashboard:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str = "supply_chain") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "supply_chain": {
                "nodes": self.store.sc_nodes.count(),
                "shipments": self.store.sc_shipments.count(),
                "orders": self.store.sc_orders.count(),
            },
            "warehouse": {
                "warehouses": self.store.sc_warehouses.count(),
                "inventory": self.store.sc_inventory.count(),
            },
            "elevator": {
                "elevators": self.store.sc_elevators.count(),
                "silos": self.store.sc_silos.count(),
            },
            "export": {
                "contracts": self.store.sc_export_contracts.count(),
                "docs": self.store.sc_export_docs.count(),
            },
            "trading": {
                "desk_orders": self.store.sc_desk_orders.count(),
                "quotes": self.store.sc_pricing.count(),
            },
            "logistics": {
                "trucks": self.store.sc_trucks.count(),
                "routes": self.store.sc_routes.count(),
                "deliveries": self.store.sc_deliveries.count(),
            },
        }[dashboard_type]
        did = _id("sc_dash")
        return self.store.sc_dashboards.save(
            did,
            {"dashboard_id": did, "dashboard_type": dashboard_type, "metrics": metrics, "generated_at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.sc_dashboards.count(), "types": self.types}


class SupplyChainKnowledge:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.types = list(REGISTRY_TYPES)

    def publish(self, *, registry_type: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if registry_type not in self.types:
            raise ValidationError(f"registry_type must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("sc_reg")
        return self.store.sc_registries.save(
            rid,
            {
                "registry_id": rid,
                "registry_type": registry_type,
                "key": key,
                "payload": payload or {},
                "graph_node": f"sc:{registry_type}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.sc_registries.count(), "types": self.types}
