"""Supply chain network, planning, and order management."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.agro_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class SupplyChainManagement:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def add_node(self, *, name: str, node_type: str = "hub", region: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("node name required")
        nid = _id("sc_node")
        return self.store.sc_nodes.save(
            nid,
            {
                "node_id": nid,
                "name": name,
                "node_type": node_type,
                "region": region,
                "created_at": _now(),
            },
        )

    def add_distribution_center(self, *, name: str, capacity_t: float = 10000.0) -> dict[str, Any]:
        if not name:
            raise ValidationError("distribution center name required")
        did = _id("sc_dc")
        return self.store.sc_dcs.save(
            did,
            {
                "dc_id": did,
                "name": name,
                "capacity_t": float(capacity_t),
                "created_at": _now(),
            },
        )

    def track_shipment(self, *, origin: str, destination: str, commodity: str, tons: float) -> dict[str, Any]:
        sid = _id("sc_ship")
        return self.store.sc_shipments.save(
            sid,
            {
                "shipment_id": sid,
                "origin": origin,
                "destination": destination,
                "commodity": commodity,
                "tons": float(tons),
                "status": "in_transit",
                "at": _now(),
            },
        )

    def supply_plan(self, *, commodity: str, tons: float, horizon_days: int = 30) -> dict[str, Any]:
        if not commodity:
            raise ValidationError("commodity required")
        pid = _id("sc_spl")
        return self.store.sc_supply_plans.save(
            pid,
            {
                "plan_id": pid,
                "commodity": commodity,
                "tons": float(tons),
                "horizon_days": int(horizon_days),
                "at": _now(),
            },
        )

    def demand_plan(self, *, commodity: str, tons: float, market: str = "EU") -> dict[str, Any]:
        if not commodity:
            raise ValidationError("commodity required")
        pid = _id("sc_dmd")
        return self.store.sc_demand_plans.save(
            pid,
            {
                "plan_id": pid,
                "commodity": commodity,
                "tons": float(tons),
                "market": market,
                "at": _now(),
            },
        )

    def create_order(self, *, buyer: str, commodity: str, tons: float, price: float = 0.0) -> dict[str, Any]:
        if not buyer or not commodity:
            raise ValidationError("buyer and commodity required")
        oid = _id("sc_ord")
        return self.store.sc_orders.save(
            oid,
            {
                "order_id": oid,
                "buyer": buyer,
                "commodity": commodity,
                "tons": float(tons),
                "price": float(price),
                "status": "open",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "nodes": self.store.sc_nodes.count(),
            "distribution_centers": self.store.sc_dcs.count(),
            "shipments": self.store.sc_shipments.count(),
            "orders": self.store.sc_orders.count(),
        }


class GrainElevatorManagement:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def register_elevator(self, *, name: str, location: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("elevator name required")
        eid = _id("sc_el")
        return self.store.sc_elevators.save(
            eid, {"elevator_id": eid, "name": name, "location": location, "created_at": _now()}
        )

    def register_silo(self, *, elevator_id: str, capacity_t: float, commodity: str = "wheat") -> dict[str, Any]:
        if self.store.sc_elevators.get(elevator_id) is None:
            raise NotFoundError("elevator", elevator_id)
        sid = _id("sc_silo")
        return self.store.sc_silos.save(
            sid,
            {
                "silo_id": sid,
                "elevator_id": elevator_id,
                "capacity_t": float(capacity_t),
                "occupied_t": 0.0,
                "commodity": commodity,
                "temp_c": 18.0,
                "humidity_pct": 55.0,
                "aeration": False,
                "created_at": _now(),
            },
        )

    def intake(self, silo_id: str, *, tons: float) -> dict[str, Any]:
        silo = self.store.sc_silos.get(silo_id)
        if silo is None:
            raise NotFoundError("silo", silo_id)
        occupied = float(silo.get("occupied_t") or 0) + float(tons)
        if occupied > float(silo["capacity_t"]):
            raise ValidationError("intake exceeds silo capacity")
        silo["occupied_t"] = occupied
        self.store.sc_silos.save(silo_id, silo)
        iid = _id("sc_int")
        return self.store.sc_intake.save(
            iid, {"intake_id": iid, "silo_id": silo_id, "tons": float(tons), "at": _now()}
        )

    def dispatch(self, silo_id: str, *, tons: float) -> dict[str, Any]:
        silo = self.store.sc_silos.get(silo_id)
        if silo is None:
            raise NotFoundError("silo", silo_id)
        occupied = float(silo.get("occupied_t") or 0) - float(tons)
        if occupied < 0:
            raise ValidationError("dispatch exceeds occupied grain")
        silo["occupied_t"] = occupied
        self.store.sc_silos.save(silo_id, silo)
        did = _id("sc_disp")
        return self.store.sc_dispatch.save(
            did, {"dispatch_id": did, "silo_id": silo_id, "tons": float(tons), "at": _now()}
        )

    def dry(self, silo_id: str, *, target_moisture_pct: float = 14.0) -> dict[str, Any]:
        if self.store.sc_silos.get(silo_id) is None:
            raise NotFoundError("silo", silo_id)
        did = _id("sc_dry")
        return self.store.sc_drying.save(
            did,
            {
                "operation_id": did,
                "silo_id": silo_id,
                "target_moisture_pct": float(target_moisture_pct),
                "status": "completed",
                "at": _now(),
            },
        )

    def clean(self, silo_id: str) -> dict[str, Any]:
        if self.store.sc_silos.get(silo_id) is None:
            raise NotFoundError("silo", silo_id)
        cid = _id("sc_cln")
        return self.store.sc_cleaning.save(
            cid, {"operation_id": cid, "silo_id": silo_id, "status": "completed", "at": _now()}
        )

    def monitor(self, silo_id: str, *, temp_c: float, humidity_pct: float, aeration: bool = False) -> dict[str, Any]:
        silo = self.store.sc_silos.get(silo_id)
        if silo is None:
            raise NotFoundError("silo", silo_id)
        silo["temp_c"] = float(temp_c)
        silo["humidity_pct"] = float(humidity_pct)
        silo["aeration"] = bool(aeration)
        silo["updated_at"] = _now()
        return self.store.sc_silos.save(silo_id, silo)

    def capacity(self, elevator_id: str) -> dict[str, Any]:
        if self.store.sc_elevators.get(elevator_id) is None:
            raise NotFoundError("elevator", elevator_id)
        silos = [s for s in self.store.sc_silos.list_all() if s.get("elevator_id") == elevator_id]
        return {
            "elevator_id": elevator_id,
            "silos": len(silos),
            "capacity_t": round(sum(float(s.get("capacity_t") or 0) for s in silos), 2),
            "occupied_t": round(sum(float(s.get("occupied_t") or 0) for s in silos), 2),
        }

    def status(self) -> dict[str, Any]:
        return {
            "elevators": self.store.sc_elevators.count(),
            "silos": self.store.sc_silos.count(),
            "intakes": self.store.sc_intake.count(),
            "dispatches": self.store.sc_dispatch.count(),
        }


class GrainQualityIntelligence:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def inspect(
        self,
        *,
        lot_id: str,
        moisture_pct: float = 14.0,
        protein_pct: float = 12.0,
        oil_pct: float = 0.0,
        foreign_material_pct: float = 1.0,
    ) -> dict[str, Any]:
        if not lot_id:
            raise ValidationError("lot_id required")
        grade = "A"
        if moisture_pct > 15 or foreign_material_pct > 2:
            grade = "B"
        if moisture_pct > 17 or foreign_material_pct > 4:
            grade = "C"
        qid = _id("sc_qi")
        return self.store.sc_quality.save(
            qid,
            {
                "inspection_id": qid,
                "lot_id": lot_id,
                "moisture_pct": float(moisture_pct),
                "protein_pct": float(protein_pct),
                "oil_pct": float(oil_pct),
                "foreign_material_pct": float(foreign_material_pct),
                "classification": grade,
                "lab_integrated": True,
                "at": _now(),
            },
        )

    def certificate(self, inspection_id: str) -> dict[str, Any]:
        insp = self.store.sc_quality.get(inspection_id)
        if insp is None:
            raise NotFoundError("inspection", inspection_id)
        cid = _id("sc_cert")
        return self.store.sc_certificates.save(
            cid,
            {
                "certificate_id": cid,
                "inspection_id": inspection_id,
                "lot_id": insp["lot_id"],
                "classification": insp["classification"],
                "issued_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "inspections": self.store.sc_quality.count(),
            "certificates": self.store.sc_certificates.count(),
        }
