"""Global network, collaboration, AI marketplace, dashboards, knowledge."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.port_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store

DASHBOARD_TYPES = ["marketplace", "carrier", "freight_exchange", "global_network", "ai_marketplace"]
REGISTRY_TYPES = ["marketplace", "carrier", "freight", "partner", "global"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class GlobalLogisticsNetwork:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def register_partner(self, *, name: str, country: str = "", role: str = "logistics") -> dict[str, Any]:
        if not name:
            raise ValidationError("partner name required")
        pid = _id("fm_prt")
        return self.store.fm_partners.save(
            pid,
            {
                "partner_id": pid,
                "name": name,
                "country": country,
                "role": role,
                "created_at": _now(),
            },
        )

    def register_port_node(self, *, name: str, unlocode: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("port node name required")
        nid = _id("fm_port")
        return self.store.fm_port_nodes.save(
            nid, {"node_id": nid, "name": name, "unlocode": unlocode, "created_at": _now()}
        )

    def register_warehouse_node(self, *, name: str, region: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("warehouse node name required")
        nid = _id("fm_whn")
        return self.store.fm_warehouse_nodes.save(
            nid, {"node_id": nid, "name": name, "region": region, "created_at": _now()}
        )

    def register_distribution_node(self, *, name: str, region: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("distribution node name required")
        nid = _id("fm_dcn")
        return self.store.fm_distribution_nodes.save(
            nid, {"node_id": nid, "name": name, "region": region, "created_at": _now()}
        )

    def register_corridor(self, *, name: str, modes: list[str] | None = None) -> dict[str, Any]:
        if not name:
            raise ValidationError("corridor name required")
        cid = _id("fm_cor")
        return self.store.fm_corridors.save(
            cid,
            {
                "corridor_id": cid,
                "name": name,
                "modes": modes or ["sea", "rail", "truck"],
                "created_at": _now(),
            },
        )

    def register_route(self, *, origin: str, destination: str, mode: str = "sea") -> dict[str, Any]:
        if not origin or not destination:
            raise ValidationError("origin and destination required")
        rid = _id("fm_rte")
        return self.store.fm_routes.save(
            rid,
            {
                "route_id": rid,
                "origin": origin,
                "destination": destination,
                "mode": mode,
                "created_at": _now(),
            },
        )

    def partner_performance(self, *, partner_id: str, otif_pct: float, score: float) -> dict[str, Any]:
        if self.store.fm_partners.get(partner_id) is None:
            raise NotFoundError("partner", partner_id)
        pid = _id("fm_perf")
        return self.store.fm_partner_perf.save(
            pid,
            {
                "performance_id": pid,
                "partner_id": partner_id,
                "otif_pct": float(otif_pct),
                "score": float(score),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "partners": self.store.fm_partners.count(),
            "port_nodes": self.store.fm_port_nodes.count(),
            "corridors": self.store.fm_corridors.count(),
            "routes": self.store.fm_routes.count(),
        }


class ShipmentCollaboration:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def workspace(self, *, shipment_ref: str, title: str = "") -> dict[str, Any]:
        if not shipment_ref:
            raise ValidationError("shipment_ref required")
        wid = _id("fm_ws")
        return self.store.fm_workspaces.save(
            wid,
            {
                "workspace_id": wid,
                "shipment_ref": shipment_ref,
                "title": title or f"Workspace {shipment_ref}",
                "created_at": _now(),
            },
        )

    def customer_portal(self, *, customer: str, workspace_id: str) -> dict[str, Any]:
        if self.store.fm_workspaces.get(workspace_id) is None:
            raise NotFoundError("workspace", workspace_id)
        pid = _id("fm_cpor")
        return self.store.fm_customer_portals.save(
            pid,
            {
                "portal_id": pid,
                "customer": customer,
                "workspace_id": workspace_id,
                "at": _now(),
            },
        )

    def carrier_portal(self, *, carrier_id: str, workspace_id: str) -> dict[str, Any]:
        if self.store.fm_workspaces.get(workspace_id) is None:
            raise NotFoundError("workspace", workspace_id)
        pid = _id("fm_kpor")
        return self.store.fm_carrier_portals.save(
            pid,
            {
                "portal_id": pid,
                "carrier_id": carrier_id,
                "workspace_id": workspace_id,
                "at": _now(),
            },
        )

    def share_document(self, *, workspace_id: str, title: str, doc_type: str = "other") -> dict[str, Any]:
        if self.store.fm_workspaces.get(workspace_id) is None:
            raise NotFoundError("workspace", workspace_id)
        did = _id("fm_doc")
        return self.store.fm_shared_docs.save(
            did,
            {
                "document_id": did,
                "workspace_id": workspace_id,
                "title": title,
                "doc_type": doc_type,
                "at": _now(),
            },
        )

    def notify(self, *, workspace_id: str, message: str, channel: str = "realtime") -> dict[str, Any]:
        if self.store.fm_workspaces.get(workspace_id) is None:
            raise NotFoundError("workspace", workspace_id)
        nid = _id("fm_ntf")
        return self.store.fm_notifications.save(
            nid,
            {
                "notification_id": nid,
                "workspace_id": workspace_id,
                "message": message,
                "channel": channel,
                "at": _now(),
            },
        )

    def collaborate(self, *, workspace_id: str, actor: str, note: str) -> dict[str, Any]:
        if self.store.fm_workspaces.get(workspace_id) is None:
            raise NotFoundError("workspace", workspace_id)
        cid = _id("fm_col")
        return self.store.fm_collab_events.save(
            cid,
            {
                "event_id": cid,
                "workspace_id": workspace_id,
                "actor": actor,
                "note": note,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "workspaces": self.store.fm_workspaces.count(),
            "shared_docs": self.store.fm_shared_docs.count(),
            "notifications": self.store.fm_notifications.count(),
        }


class AILogisticsMarketplace:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def recommend_carrier(self, *, origin: str, destination: str, mode: str = "sea") -> dict[str, Any]:
        rid = _id("fm_arec")
        return self.store.fm_ai_recommend.save(
            rid,
            {
                "recommendation_id": rid,
                "origin": origin,
                "destination": destination,
                "mode": mode,
                "confidence": 0.88,
                "at": _now(),
            },
        )

    def match_freight(self, *, request_id: str, carrier_id: str) -> dict[str, Any]:
        mid = _id("fm_amatch")
        return self.store.fm_ai_match.save(
            mid,
            {
                "match_id": mid,
                "request_id": request_id,
                "carrier_id": carrier_id,
                "score": 0.91,
                "at": _now(),
            },
        )

    def dynamic_pricing(self, *, corridor: str, baseline: float) -> dict[str, Any]:
        pid = _id("fm_aprice")
        return self.store.fm_ai_pricing.save(
            pid,
            {
                "pricing_id": pid,
                "corridor": corridor,
                "baseline": float(baseline),
                "dynamic_price": round(float(baseline) * 1.07, 2),
                "at": _now(),
            },
        )

    def capacity_predict(self, *, corridor: str, teu: float) -> dict[str, Any]:
        cid = _id("fm_acap")
        return self.store.fm_ai_capacity.save(
            cid,
            {
                "prediction_id": cid,
                "corridor": corridor,
                "teu": float(teu),
                "utilization_pct": 78.0,
                "at": _now(),
            },
        )

    def demand_forecast(self, *, corridor: str, days: int = 30, baseline: float = 1000.0) -> dict[str, Any]:
        fid = _id("fm_admd")
        return self.store.fm_ai_demand.save(
            fid,
            {
                "forecast_id": fid,
                "corridor": corridor,
                "days": int(days),
                "predicted_teu": round(float(baseline) * 1.11, 2),
                "at": _now(),
            },
        )

    def optimize_route(self, *, origin: str, destination: str, mode: str = "multimodal") -> dict[str, Any]:
        oid = _id("fm_aroute")
        return self.store.fm_ai_routes.save(
            oid,
            {
                "route_id": oid,
                "origin": origin,
                "destination": destination,
                "mode": mode,
                "eta_hours": 96.0,
                "optimized": True,
                "at": _now(),
            },
        )

    def optimize_cost(self, *, booking_ref: str, baseline_cost: float) -> dict[str, Any]:
        oid = _id("fm_acost")
        return self.store.fm_ai_cost.save(
            oid,
            {
                "optimization_id": oid,
                "booking_ref": booking_ref,
                "baseline_cost": float(baseline_cost),
                "optimized_cost": round(float(baseline_cost) * 0.9, 2),
                "at": _now(),
            },
        )

    def fraud_detect(self, *, subject_ref: str, anomaly_score: float) -> dict[str, Any]:
        score = float(anomaly_score)
        if score < 0 or score > 1:
            raise ValidationError("anomaly_score must be 0..1")
        fid = _id("fm_afraud")
        return self.store.fm_ai_fraud.save(
            fid,
            {
                "detection_id": fid,
                "subject_ref": subject_ref,
                "anomaly_score": score,
                "flagged": score >= 0.6,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "recommendations": self.store.fm_ai_recommend.count(),
            "matches": self.store.fm_ai_match.count(),
            "fraud": self.store.fm_ai_fraud.count(),
        }


class MarketplaceDashboard:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str = "marketplace") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "marketplace": {
                "listings": self.store.fm_cargo_listings.count(),
                "matches": self.store.fm_matches.count(),
            },
            "carrier": {
                "carriers": self.store.fm_carriers.count(),
                "ratings": self.store.fm_ratings.count(),
            },
            "freight_exchange": {
                "spots": self.store.fm_spots.count(),
                "bookings": self.store.fm_bookings.count(),
            },
            "global_network": {
                "partners": self.store.fm_partners.count(),
                "routes": self.store.fm_routes.count(),
            },
            "ai_marketplace": {
                "recommendations": self.store.fm_ai_recommend.count(),
                "fraud": self.store.fm_ai_fraud.count(),
            },
        }[dashboard_type]
        did = _id("fm_dash")
        return self.store.fm_dashboards.save(
            did,
            {"dashboard_id": did, "dashboard_type": dashboard_type, "metrics": metrics, "generated_at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.fm_dashboards.count(), "types": self.types}


class MarketplaceKnowledge:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store
        self.types = list(REGISTRY_TYPES)

    def publish(self, *, registry_type: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if registry_type not in self.types:
            raise ValidationError(f"registry_type must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("fm_reg")
        return self.store.fm_registries.save(
            rid,
            {
                "registry_id": rid,
                "registry_type": registry_type,
                "key": key,
                "payload": payload or {},
                "graph_node": f"fm:{registry_type}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.fm_registries.count(), "types": self.types}
