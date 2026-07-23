"""Multimodal, inland, shipment, and AI logistics."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.port_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store

TRANSPORT_MODES = ["sea", "rail", "truck", "barge", "air"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class MultimodalTransport:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def create_chain(self, *, name: str, legs: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        if not name:
            raise ValidationError("chain name required")
        cid = _id("ml_chn")
        return self.store.ml_chains.save(
            cid,
            {
                "chain_id": cid,
                "name": name,
                "legs": legs or [],
                "status": "planned",
                "created_at": _now(),
            },
        )

    def mode_transfer(self, *, chain_id: str, from_mode: str, to_mode: str, location: str) -> dict[str, Any]:
        if self.store.ml_chains.get(chain_id) is None:
            raise NotFoundError("chain", chain_id)
        if from_mode not in TRANSPORT_MODES or to_mode not in TRANSPORT_MODES:
            raise ValidationError(f"modes must be in {TRANSPORT_MODES}")
        tid = _id("ml_xfer")
        return self.store.ml_transfers.save(
            tid,
            {
                "transfer_id": tid,
                "chain_id": chain_id,
                "from_mode": from_mode,
                "to_mode": to_mode,
                "location": location,
                "at": _now(),
            },
        )

    def container_transfer(self, *, chain_id: str, container_ref: str, location: str) -> dict[str, Any]:
        if self.store.ml_chains.get(chain_id) is None:
            raise NotFoundError("chain", chain_id)
        tid = _id("ml_ctx")
        return self.store.ml_container_xfers.save(
            tid,
            {
                "transfer_id": tid,
                "chain_id": chain_id,
                "container_ref": container_ref,
                "location": location,
                "at": _now(),
            },
        )

    def intermodal_terminal(self, *, name: str, modes: list[str] | None = None) -> dict[str, Any]:
        if not name:
            raise ValidationError("terminal name required")
        tid = _id("ml_imt")
        return self.store.ml_intermodal.save(
            tid,
            {
                "terminal_id": tid,
                "name": name,
                "modes": modes or ["rail", "truck"],
                "created_at": _now(),
            },
        )

    def cross_dock(self, *, terminal_id: str, inbound: str, outbound: str) -> dict[str, Any]:
        if self.store.ml_intermodal.get(terminal_id) is None:
            raise NotFoundError("intermodal_terminal", terminal_id)
        cid = _id("ml_xdock")
        return self.store.ml_crossdock.save(
            cid,
            {
                "crossdock_id": cid,
                "terminal_id": terminal_id,
                "inbound": inbound,
                "outbound": outbound,
                "at": _now(),
            },
        )

    def consolidate(self, *, shipment_refs: list[str], destination: str) -> dict[str, Any]:
        if not shipment_refs:
            raise ValidationError("shipment_refs required")
        cid = _id("ml_cons")
        return self.store.ml_consolidations.save(
            cid,
            {
                "consolidation_id": cid,
                "shipment_refs": shipment_refs,
                "destination": destination,
                "at": _now(),
            },
        )

    def optimize_transport(self, *, chain_id: str) -> dict[str, Any]:
        if self.store.ml_chains.get(chain_id) is None:
            raise NotFoundError("chain", chain_id)
        oid = _id("ml_topt")
        return self.store.ml_transport_opts.save(
            oid,
            {
                "optimization_id": oid,
                "chain_id": chain_id,
                "cost_saving_pct": 11.0,
                "time_saving_hours": 6.5,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "chains": self.store.ml_chains.count(),
            "transfers": self.store.ml_transfers.count(),
            "intermodal_terminals": self.store.ml_intermodal.count(),
        }


class InlandLogistics:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def register_dry_port(self, *, name: str, region: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("dry port name required")
        did = _id("ml_dry")
        return self.store.ml_dry_ports.save(
            did, {"dry_port_id": did, "name": name, "region": region, "created_at": _now()}
        )

    def register_dc(self, *, name: str, capacity_teu: float = 5000.0) -> dict[str, Any]:
        if not name:
            raise ValidationError("distribution center name required")
        cid = _id("ml_dc")
        return self.store.ml_dcs.save(
            cid, {"dc_id": cid, "name": name, "capacity_teu": float(capacity_teu), "created_at": _now()}
        )

    def register_hub(self, *, name: str) -> dict[str, Any]:
        if not name:
            raise ValidationError("hub name required")
        hid = _id("ml_hub")
        return self.store.ml_hubs.save(
            hid, {"hub_id": hid, "name": name, "created_at": _now()}
        )

    def redistribute(self, *, from_site: str, to_site: str, teu: float) -> dict[str, Any]:
        rid = _id("ml_rdist")
        return self.store.ml_redistributions.save(
            rid,
            {
                "redistribution_id": rid,
                "from_site": from_site,
                "to_site": to_site,
                "teu": float(teu),
                "at": _now(),
            },
        )

    def coordinate_storage(self, *, site: str, teu: float) -> dict[str, Any]:
        cid = _id("ml_stor")
        return self.store.ml_storage_coord.save(
            cid, {"coord_id": cid, "site": site, "teu": float(teu), "at": _now()}
        )

    def status(self) -> dict[str, Any]:
        return {
            "dry_ports": self.store.ml_dry_ports.count(),
            "distribution_centers": self.store.ml_dcs.count(),
            "hubs": self.store.ml_hubs.count(),
        }


class ShipmentManagement:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def register(self, *, reference: str, origin: str, destination: str) -> dict[str, Any]:
        if not reference:
            raise ValidationError("shipment reference required")
        sid = _id("ml_shp")
        return self.store.ml_shipments.save(
            sid,
            {
                "shipment_id": sid,
                "reference": reference,
                "origin": origin,
                "destination": destination,
                "status": "created",
                "created_at": _now(),
            },
        )

    def track(self, shipment_id: str, *, status: str, location: str = "") -> dict[str, Any]:
        shp = self.store.ml_shipments.get(shipment_id)
        if shp is None:
            raise NotFoundError("shipment", shipment_id)
        shp["status"] = status
        shp["location"] = location
        shp["updated_at"] = _now()
        self.store.ml_shipments.save(shipment_id, shp)
        eid = _id("ml_sevt")
        return self.store.ml_shipment_events.save(
            eid,
            {
                "event_id": eid,
                "shipment_id": shipment_id,
                "status": status,
                "location": location,
                "at": _now(),
            },
        )

    def document(self, shipment_id: str, *, doc_type: str, title: str) -> dict[str, Any]:
        if self.store.ml_shipments.get(shipment_id) is None:
            raise NotFoundError("shipment", shipment_id)
        did = _id("ml_doc")
        return self.store.ml_shipment_docs.save(
            did,
            {
                "document_id": did,
                "shipment_id": shipment_id,
                "doc_type": doc_type,
                "title": title,
                "at": _now(),
            },
        )

    def eta(self, shipment_id: str, *, hours: float) -> dict[str, Any]:
        if self.store.ml_shipments.get(shipment_id) is None:
            raise NotFoundError("shipment", shipment_id)
        eid = _id("ml_eta")
        return self.store.ml_shipment_eta.save(
            eid, {"eta_id": eid, "shipment_id": shipment_id, "eta_hours": float(hours), "at": _now()}
        )

    def schedule_delivery(self, shipment_id: str, *, window_start: str, window_end: str = "") -> dict[str, Any]:
        if self.store.ml_shipments.get(shipment_id) is None:
            raise NotFoundError("shipment", shipment_id)
        sid = _id("ml_del")
        return self.store.ml_deliveries.save(
            sid,
            {
                "delivery_id": sid,
                "shipment_id": shipment_id,
                "window_start": window_start,
                "window_end": window_end,
                "at": _now(),
            },
        )

    def proof_of_delivery(self, shipment_id: str, *, signed_by: str) -> dict[str, Any]:
        if self.store.ml_shipments.get(shipment_id) is None:
            raise NotFoundError("shipment", shipment_id)
        pid = _id("ml_pod")
        shp = self.store.ml_shipments.get(shipment_id)
        shp["status"] = "delivered"
        self.store.ml_shipments.save(shipment_id, shp)
        return self.store.ml_pods.save(
            pid,
            {
                "pod_id": pid,
                "shipment_id": shipment_id,
                "signed_by": signed_by,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "shipments": self.store.ml_shipments.count(),
            "events": self.store.ml_shipment_events.count(),
            "pods": self.store.ml_pods.count(),
        }


class AILogisticsIntelligence:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def demand_forecast(self, *, corridor: str, teu: float, days: int = 30) -> dict[str, Any]:
        fid = _id("ml_dfc")
        return self.store.ml_ai_demand.save(
            fid,
            {
                "forecast_id": fid,
                "corridor": corridor,
                "teu": float(teu),
                "days": int(days),
                "predicted_teu": round(float(teu) * 1.08, 2),
                "at": _now(),
            },
        )

    def optimize_route(self, *, origin: str, destination: str, mode: str = "truck") -> dict[str, Any]:
        if mode not in TRANSPORT_MODES:
            raise ValidationError(f"mode must be one of {TRANSPORT_MODES}")
        rid = _id("ml_aroute")
        return self.store.ml_ai_routes.save(
            rid,
            {
                "route_id": rid,
                "origin": origin,
                "destination": destination,
                "mode": mode,
                "eta_hours": 14.0 if mode == "truck" else 28.0,
                "optimized": True,
                "at": _now(),
            },
        )

    def optimize_fleet(self, *, fleet_size: int) -> dict[str, Any]:
        oid = _id("ml_afleet")
        return self.store.ml_ai_fleet.save(
            oid,
            {
                "optimization_id": oid,
                "fleet_size": int(fleet_size),
                "utilization_gain_pct": 9.5,
                "at": _now(),
            },
        )

    def traffic_prediction(self, *, corridor: str) -> dict[str, Any]:
        tid = _id("ml_traf")
        return self.store.ml_ai_traffic.save(
            tid, {"prediction_id": tid, "corridor": corridor, "congestion_index": 0.42, "at": _now()}
        )

    def capacity_forecast(self, *, node: str, teu: float) -> dict[str, Any]:
        cid = _id("ml_acap")
        return self.store.ml_ai_capacity.save(
            cid,
            {
                "forecast_id": cid,
                "node": node,
                "teu": float(teu),
                "peak_utilization_pct": 78.0,
                "at": _now(),
            },
        )

    def cost_optimize(self, *, shipment_id: str, baseline_cost: float) -> dict[str, Any]:
        oid = _id("ml_acost")
        return self.store.ml_ai_cost.save(
            oid,
            {
                "optimization_id": oid,
                "shipment_id": shipment_id,
                "baseline_cost": float(baseline_cost),
                "optimized_cost": round(float(baseline_cost) * 0.91, 2),
                "at": _now(),
            },
        )

    def delay_predict(self, *, shipment_id: str, risk: float) -> dict[str, Any]:
        risk = float(risk)
        if risk < 0 or risk > 1:
            raise ValidationError("risk must be 0..1")
        did = _id("ml_adel")
        return self.store.ml_ai_delay.save(
            did,
            {
                "prediction_id": did,
                "shipment_id": shipment_id,
                "risk": risk,
                "expected_delay_hours": round(risk * 12, 1),
                "at": _now(),
            },
        )

    def carbon_analytics(self, *, shipment_id: str, ton_km: float) -> dict[str, Any]:
        cid = _id("ml_co2")
        return self.store.ml_ai_carbon.save(
            cid,
            {
                "analytics_id": cid,
                "shipment_id": shipment_id,
                "ton_km": float(ton_km),
                "co2_kg": round(float(ton_km) * 0.062, 2),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "demand_forecasts": self.store.ml_ai_demand.count(),
            "routes": self.store.ml_ai_routes.count(),
            "carbon": self.store.ml_ai_carbon.count(),
        }
