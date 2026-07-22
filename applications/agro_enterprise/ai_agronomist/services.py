"""Dashboards and knowledge for AI Agronomist."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.agro_enterprise.shared.exceptions import ValidationError
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store

DASHBOARD_TYPES = [
    "agronomist",
    "decision_support",
    "forecast",
    "optimization",
    "executive_intelligence",
]
REGISTRY_TYPES = ["agronomist", "decision", "planning", "forecast", "optimization"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AIAgronomistDashboard:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str = "agronomist") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "agronomist": {
                "consultations": self.store.aa_consultations.count(),
                "advisories": self.store.aa_advisories.count(),
            },
            "decision_support": {
                "decisions": self.store.aa_decisions.count(),
                "scenarios": self.store.aa_scenarios.count(),
                "recommendations": self.store.aa_recommendations.count(),
            },
            "forecast": {"forecasts": self.store.aa_forecasts.count()},
            "optimization": {"optimizations": self.store.aa_optimizations.count()},
            "executive_intelligence": {
                "briefings": self.store.aa_briefings.count(),
                "strategies": self.store.aa_strategies.count(),
                "plans": self.store.aa_plans.count(),
            },
        }[dashboard_type]
        did = _id("aa_dash")
        return self.store.aa_dashboards.save(
            did,
            {"dashboard_id": did, "dashboard_type": dashboard_type, "metrics": metrics, "generated_at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.aa_dashboards.count(), "types": self.types}


class AIAgronomistKnowledge:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.types = list(REGISTRY_TYPES)

    def publish(self, *, registry_type: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if registry_type not in self.types:
            raise ValidationError(f"registry_type must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("aa_reg")
        return self.store.aa_registries.save(
            rid,
            {
                "registry_id": rid,
                "registry_type": registry_type,
                "key": key,
                "payload": payload or {},
                "graph_node": f"aa:{registry_type}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.aa_registries.count(), "types": self.types}
