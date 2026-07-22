"""Warehouse, processing, logistics, export & trading."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.agro_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store

INCOTERMS = ["FOB", "CIF", "CFR", "EXW", "DAP", "DDP"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class WarehouseManagement:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def register_warehouse(self, *, name: str, cold_storage: bool = False) -> dict[str, Any]:
        if not name:
            raise ValidationError("warehouse name required")
        wid = _id("sc_wh")
        return self.store.sc_warehouses.save(
            wid,
            {
                "warehouse_id": wid,
                "name": name,
                "cold_storage": bool(cold_storage),
                "created_at": _now(),
            },
        )

    def add_inventory(self, *, warehouse_id: str, sku: str, tons: float, lot: str = "", batch: str = "") -> dict[str, Any]:
        if self.store.sc_warehouses.get(warehouse_id) is None:
            raise NotFoundError("warehouse", warehouse_id)
        if not sku:
            raise ValidationError("sku required")
        iid = _id("sc_inv")
        barcode = f"BC-{uuid.uuid4().hex[:8].upper()}"
        rfid = f"RFID-{uuid.uuid4().hex[:8].upper()}"
        return self.store.sc_inventory.save(
            iid,
            {
                "inventory_id": iid,
                "warehouse_id": warehouse_id,
                "sku": sku,
                "tons": float(tons),
                "lot": lot or _id("lot"),
                "batch": batch or _id("batch"),
                "barcode": barcode,
                "rfid": rfid,
                "at": _now(),
            },
        )

    def optimize(self, warehouse_id: str) -> dict[str, Any]:
        if self.store.sc_warehouses.get(warehouse_id) is None:
            raise NotFoundError("warehouse", warehouse_id)
        items = [i for i in self.store.sc_inventory.list_all() if i.get("warehouse_id") == warehouse_id]
        oid = _id("sc_wopt")
        return self.store.sc_wh_opts.save(
            oid,
            {
                "optimization_id": oid,
                "warehouse_id": warehouse_id,
                "sku_count": len(items),
                "total_tons": round(sum(float(i.get("tons") or 0) for i in items), 2),
                "strategy": "abc_slotting",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "warehouses": self.store.sc_warehouses.count(),
            "inventory_items": self.store.sc_inventory.count(),
        }


class ProcessingManagement:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def register_plant(self, *, name: str, capacity_t_day: float = 500.0) -> dict[str, Any]:
        if not name:
            raise ValidationError("plant name required")
        pid = _id("sc_plant")
        return self.store.sc_plants.save(
            pid,
            {
                "plant_id": pid,
                "name": name,
                "capacity_t_day": float(capacity_t_day),
                "created_at": _now(),
            },
        )

    def run_operation(self, *, plant_id: str, operation: str, tons: float) -> dict[str, Any]:
        if self.store.sc_plants.get(plant_id) is None:
            raise NotFoundError("plant", plant_id)
        allowed = {"cleaning", "drying", "sorting", "packaging"}
        if operation not in allowed:
            raise ValidationError(f"operation must be one of {sorted(allowed)}")
        oid = _id("sc_pop")
        return self.store.sc_processing.save(
            oid,
            {
                "operation_id": oid,
                "plant_id": plant_id,
                "operation": operation,
                "tons": float(tons),
                "status": "completed",
                "at": _now(),
            },
        )

    def production_plan(self, *, plant_id: str, commodity: str, tons: float) -> dict[str, Any]:
        if self.store.sc_plants.get(plant_id) is None:
            raise NotFoundError("plant", plant_id)
        pid = _id("sc_pplan")
        return self.store.sc_prod_plans.save(
            pid,
            {
                "plan_id": pid,
                "plant_id": plant_id,
                "commodity": commodity,
                "tons": float(tons),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "plants": self.store.sc_plants.count(),
            "operations": self.store.sc_processing.count(),
        }


class AgroLogistics:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def register_truck(self, *, plate: str, capacity_t: float = 25.0) -> dict[str, Any]:
        if not plate:
            raise ValidationError("plate required")
        tid = _id("sc_trk")
        return self.store.sc_trucks.save(
            tid, {"truck_id": tid, "plate": plate, "capacity_t": float(capacity_t), "created_at": _now()}
        )

    def register_rail(self, *, wagon: str, capacity_t: float = 60.0) -> dict[str, Any]:
        if not wagon:
            raise ValidationError("wagon required")
        rid = _id("sc_rail")
        return self.store.sc_rail.save(
            rid, {"rail_id": rid, "wagon": wagon, "capacity_t": float(capacity_t), "created_at": _now()}
        )

    def register_container(self, *, code: str, teu: float = 1.0) -> dict[str, Any]:
        if not code:
            raise ValidationError("container code required")
        cid = _id("sc_ctr")
        return self.store.sc_containers.save(
            cid, {"container_id": cid, "code": code, "teu": float(teu), "created_at": _now()}
        )

    def optimize_route(self, *, origin: str, destination: str, mode: str = "truck") -> dict[str, Any]:
        if not origin or not destination:
            raise ValidationError("origin and destination required")
        rid = _id("sc_route")
        eta_hours = 12 if mode == "truck" else 36 if mode == "rail" else 72
        return self.store.sc_routes.save(
            rid,
            {
                "route_id": rid,
                "origin": origin,
                "destination": destination,
                "mode": mode,
                "eta_hours": eta_hours,
                "optimized": True,
                "at": _now(),
            },
        )

    def freight_plan(self, *, commodity: str, tons: float, mode: str = "truck") -> dict[str, Any]:
        fid = _id("sc_frt")
        return self.store.sc_freight.save(
            fid,
            {
                "freight_id": fid,
                "commodity": commodity,
                "tons": float(tons),
                "mode": mode,
                "status": "planned",
                "at": _now(),
            },
        )

    def track_cargo(self, *, shipment_ref: str, lat: float = 0.0, lon: float = 0.0) -> dict[str, Any]:
        tid = _id("sc_cargo")
        return self.store.sc_cargo.save(
            tid,
            {
                "tracking_id": tid,
                "shipment_ref": shipment_ref,
                "lat": float(lat),
                "lon": float(lon),
                "at": _now(),
            },
        )

    def schedule_delivery(self, *, shipment_ref: str, window_start: str, window_end: str = "") -> dict[str, Any]:
        sid = _id("sc_del")
        return self.store.sc_deliveries.save(
            sid,
            {
                "delivery_id": sid,
                "shipment_ref": shipment_ref,
                "window_start": window_start,
                "window_end": window_end,
                "eta_predicted": True,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "trucks": self.store.sc_trucks.count(),
            "rail": self.store.sc_rail.count(),
            "containers": self.store.sc_containers.count(),
            "routes": self.store.sc_routes.count(),
        }


class ExportTrading:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def create_contract(
        self,
        *,
        buyer: str,
        commodity: str,
        tons: float,
        price: float,
        incoterm: str = "FOB",
    ) -> dict[str, Any]:
        if not buyer or not commodity:
            raise ValidationError("buyer and commodity required")
        if incoterm not in INCOTERMS:
            raise ValidationError(f"incoterm must be one of {INCOTERMS}")
        cid = _id("sc_xctr")
        return self.store.sc_export_contracts.save(
            cid,
            {
                "contract_id": cid,
                "buyer": buyer,
                "commodity": commodity,
                "tons": float(tons),
                "price": float(price),
                "incoterm": incoterm,
                "status": "active",
                "at": _now(),
            },
        )

    def register_buyer(self, *, name: str, country: str) -> dict[str, Any]:
        if not name:
            raise ValidationError("buyer name required")
        bid = _id("sc_xbuy")
        return self.store.sc_intl_buyers.save(
            bid, {"buyer_id": bid, "name": name, "country": country, "created_at": _now()}
        )

    def price_quote(self, *, commodity: str, market: str = "CBOT") -> dict[str, Any]:
        if not commodity:
            raise ValidationError("commodity required")
        base = {"wheat": 240.0, "corn": 200.0, "barley": 180.0, "soy": 420.0}.get(commodity.lower(), 220.0)
        qid = _id("sc_px")
        return self.store.sc_pricing.save(
            qid,
            {
                "quote_id": qid,
                "commodity": commodity,
                "market": market,
                "price_usd_t": base,
                "at": _now(),
            },
        )

    def export_docs(self, *, contract_id: str) -> dict[str, Any]:
        if self.store.sc_export_contracts.get(contract_id) is None:
            raise NotFoundError("export_contract", contract_id)
        did = _id("sc_xdoc")
        return self.store.sc_export_docs.save(
            did,
            {
                "doc_pack_id": did,
                "contract_id": contract_id,
                "documents": ["invoice", "packing_list", "bill_of_lading", "phytosanitary"],
                "customs_ready": True,
                "at": _now(),
            },
        )

    def trading_desk_order(self, *, side: str, commodity: str, tons: float, price: float) -> dict[str, Any]:
        if side not in ("buy", "sell"):
            raise ValidationError("side must be buy or sell")
        oid = _id("sc_desk")
        return self.store.sc_desk_orders.save(
            oid,
            {
                "desk_order_id": oid,
                "side": side,
                "commodity": commodity,
                "tons": float(tons),
                "price": float(price),
                "status": "working",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "export_contracts": self.store.sc_export_contracts.count(),
            "buyers": self.store.sc_intl_buyers.count(),
            "desk_orders": self.store.sc_desk_orders.count(),
        }
