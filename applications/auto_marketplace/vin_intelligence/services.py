"""Knowledge graph, integrations, dashboards — Sprint 13.1."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

GRAPH_TYPES = ["vehicle", "owner", "dealer", "repair", "part", "insurance"]
INTEGRATION_CHANNELS = [
    "government_registries",
    "insurance_apis",
    "dealer_apis",
    "vin_providers",
    "auction_providers",
    "maintenance_systems",
    "telematics",
]
DASHBOARD_TYPES = ["vin", "fraud", "market", "passport"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class KnowledgeGraph:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def upsert_node(self, *, graph: str, node_id: str, label: str, props: dict[str, Any] | None = None) -> dict[str, Any]:
        if graph not in GRAPH_TYPES:
            raise ValidationError(f"graph must be one of {GRAPH_TYPES}")
        key = f"{graph}:{node_id}"
        node = {
            "key": key,
            "graph": graph,
            "node_id": node_id,
            "label": label,
            "props": props or {},
            "updated_at": _now(),
        }
        return self.store.vi_graph_nodes.save(key, node)

    def link(self, *, graph: str, source: str, target: str, relation: str) -> dict[str, Any]:
        if graph not in GRAPH_TYPES:
            raise ValidationError(f"graph must be one of {GRAPH_TYPES}")
        eid = _id("viedge")
        edge = {
            "edge_id": eid,
            "graph": graph,
            "source": source,
            "target": target,
            "relation": relation,
            "at": _now(),
        }
        return self.store.vi_graph_edges.save(eid, edge)

    def status(self) -> dict[str, Any]:
        return {
            "nodes": self.store.vi_graph_nodes.count(),
            "edges": self.store.vi_graph_edges.count(),
            "graphs": GRAPH_TYPES,
        }


class VINIntegrations:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.channels = list(INTEGRATION_CHANNELS)

    def connect(self, *, channel: str, endpoint: str = "") -> dict[str, Any]:
        if channel not in self.channels:
            raise ValidationError(f"channel must be one of {self.channels}")
        iid = _id("viint")
        record = {
            "integration_id": iid,
            "channel": channel,
            "endpoint": endpoint,
            "status": "connected",
            "connected_at": _now(),
        }
        return self.store.vi_integrations.save(iid, record)

    def list_connections(self) -> list[dict[str, Any]]:
        return [i for i in self.store.vi_integrations.list_all() if i.get("status") == "connected"]

    def status(self) -> dict[str, Any]:
        return {"connected": len(self.list_connections()), "channels": self.channels}


class VINDashboard:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str) -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        if dashboard_type == "vin":
            widgets: dict[str, Any] = {
                "decodes": self.store.vi_decodes.count(),
                "passports": self.store.vi_passports.count(),
            }
        elif dashboard_type == "fraud":
            frauds = [a for a in self.store.vi_analyses.list_all() if a.get("kind") == "fraud_detection"]
            widgets = {
                "fraud_checks": len(frauds),
                "flagged": len([f for f in frauds if f.get("fraudulent")]),
            }
        elif dashboard_type == "market":
            values = [a for a in self.store.vi_analyses.list_all() if a.get("kind") == "market_value"]
            avg = round(sum(float(v.get("estimate") or 0) for v in values) / max(1, len(values)), 2)
            widgets = {"estimates": len(values), "avg_value": avg}
        else:
            widgets = {
                "passports": self.store.vi_passports.count(),
                "history_records": self.store.vi_history.count(),
                "recommendations": self.store.vi_recommendations.count(),
            }
        did = _id("vidash")
        board = {
            "dashboard_id": did,
            "dashboard_type": dashboard_type,
            "widgets": widgets,
            "rendered_at": _now(),
        }
        return self.store.vi_dashboards.save(did, board)

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.vi_dashboards.count(), "types": self.types}
