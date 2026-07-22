"""Dashboards and knowledge for controlled environment."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.agro_enterprise.shared.exceptions import ValidationError
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store

DASHBOARD_TYPES = ["greenhouse", "livestock", "poultry", "aquaculture", "biosecurity", "production"]
REGISTRY_TYPES = ["greenhouse", "livestock", "poultry", "aquaculture", "biosecurity"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CEADashboard:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str = "greenhouse") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "greenhouse": {"greenhouses": self.store.ce_greenhouses.count(), "zones": self.store.ce_zones.count()},
            "livestock": {"animals": self.store.ce_animals.count(), "milk": self.store.ce_milk.count()},
            "poultry": {"flocks": self.store.ce_flocks.count(), "eggs": self.store.ce_eggs.count()},
            "aquaculture": {"farms": self.store.ce_fish_farms.count(), "water": self.store.ce_aqua_water.count()},
            "biosecurity": {"incidents": self.store.ce_incidents.count(), "quarantine": self.store.ce_quarantine.count()},
            "production": {
                "gh_yield_kg": round(sum(float(y.get("kg") or 0) for y in self.store.ce_yields.list_all()), 2),
                "optimizations": self.store.ce_ai_opts.count(),
            },
        }[dashboard_type]
        did = _id("ce_dash")
        return self.store.ce_dashboards.save(
            did,
            {"dashboard_id": did, "dashboard_type": dashboard_type, "metrics": metrics, "generated_at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.ce_dashboards.count(), "types": self.types}


class CEAKnowledge:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.types = list(REGISTRY_TYPES)

    def publish(self, *, registry_type: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if registry_type not in self.types:
            raise ValidationError(f"registry_type must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("ce_reg")
        return self.store.ce_registries.save(
            rid,
            {
                "registry_id": rid,
                "registry_type": registry_type,
                "key": key,
                "payload": payload or {},
                "graph_node": f"cea:{registry_type}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.ce_registries.count(), "types": self.types}
