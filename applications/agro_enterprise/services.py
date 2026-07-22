"""Knowledge system and executive dashboards."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.agro_enterprise.config import DEFAULT_CONFIG
from applications.agro_enterprise.shared.exceptions import ValidationError
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AgroKnowledge:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.bases = list(DEFAULT_CONFIG.knowledge_bases)

    def publish(self, *, base: str, title: str, body: str = "", tags: list[str] | None = None) -> dict[str, Any]:
        if base not in self.bases:
            raise ValidationError(f"base must be one of {self.bases}")
        if not title:
            raise ValidationError("title required")
        kid = _id("ae_kb")
        return self.store.knowledge.save(
            kid,
            {
                "article_id": kid,
                "base": base,
                "title": title,
                "body": body,
                "tags": tags or [],
                "graph_node": f"agro:{base}:{kid}",
                "created_at": _now(),
            },
        )

    def search(self, *, query: str) -> list[dict[str, Any]]:
        q = (query or "").lower()
        return [
            a
            for a in self.store.knowledge.list_all()
            if q in (a.get("title") or "").lower() or q in (a.get("body") or "").lower()
        ]

    def status(self) -> dict[str, Any]:
        return {"articles": self.store.knowledge.count(), "bases": self.bases}


class AgroDashboard:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.types = list(DEFAULT_CONFIG.dashboard_types)

    def render(self, *, dashboard_type: str = "executive") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics_map = {
            "marketplace": {
                "listings": self.store.listings.count(),
                "orders": self.store.orders.count(),
                "suppliers": self.store.suppliers.count(),
            },
            "farm": {
                "farms": self.store.farms.count(),
                "farmland": self.store.farmland.count(),
                "equipment": self.store.equipment.count(),
            },
            "production": {
                "crops": self.store.crops.count(),
                "yield_plans": self.store.yield_plans.count(),
                "harvest_plans": self.store.harvest_plans.count(),
            },
            "sales": {
                "orders": self.store.orders.count(),
                "contracts": self.store.contracts.count(),
                "leads": self.store.leads.count(),
            },
            "executive": {
                "farms": self.store.farms.count(),
                "listings": self.store.listings.count(),
                "crops": self.store.crops.count(),
                "crm_contacts": self.store.crm_contacts.count(),
                "knowledge": self.store.knowledge.count(),
            },
        }
        did = _id("ae_dash")
        board = {
            "dashboard_id": did,
            "dashboard_type": dashboard_type,
            "metrics": metrics_map[dashboard_type],
            "kpis": {
                "marketplace_liquidity": self.store.orders.count(),
                "certified_farms": self.store.certifications.count(),
                "planned_yield_t": round(
                    sum(float(y.get("expected_total_t") or 0) for y in self.store.yield_plans.list_all()), 2
                ),
            },
            "generated_at": _now(),
        }
        return self.store.dashboards.save(did, board)

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.dashboards.count(), "types": self.types}
