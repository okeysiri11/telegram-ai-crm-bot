"""Inventory intelligence, warehouse automation, and AI."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.port_enterprise.shared.exceptions import ValidationError
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store

DASHBOARD_TYPES = ["warehouse", "distribution", "fez", "inventory", "ai_warehouse"]
REGISTRY_TYPES = ["warehouse", "distribution", "fez", "inventory", "automation"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class InventoryIntelligence:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def upsert_item(self, *, warehouse_id: str, sku: str, qty: float) -> dict[str, Any]:
        if not sku:
            raise ValidationError("sku required")
        iid = _id("wd_inv")
        return self.store.wd_inventory.save(
            iid,
            {
                "inventory_id": iid,
                "warehouse_id": warehouse_id,
                "sku": sku,
                "qty": float(qty),
                "updated_at": _now(),
            },
        )

    def track_batch(self, *, sku: str, batch_no: str, qty: float) -> dict[str, Any]:
        if not batch_no:
            raise ValidationError("batch_no required")
        bid = _id("wd_batch")
        return self.store.wd_batches.save(
            bid, {"batch_id": bid, "sku": sku, "batch_no": batch_no, "qty": float(qty), "at": _now()}
        )

    def track_lot(self, *, sku: str, lot_no: str, qty: float) -> dict[str, Any]:
        if not lot_no:
            raise ValidationError("lot_no required")
        lid = _id("wd_lot")
        return self.store.wd_lots.save(
            lid, {"lot_id": lid, "sku": sku, "lot_no": lot_no, "qty": float(qty), "at": _now()}
        )

    def track_serial(self, *, sku: str, serial_no: str) -> dict[str, Any]:
        if not serial_no:
            raise ValidationError("serial_no required")
        sid = _id("wd_ser")
        return self.store.wd_serials.save(
            sid, {"serial_id": sid, "sku": sku, "serial_no": serial_no, "at": _now()}
        )

    def barcode(self, *, sku: str, code: str) -> dict[str, Any]:
        if not code:
            raise ValidationError("barcode required")
        bid = _id("wd_bc")
        return self.store.wd_barcodes.save(
            bid, {"barcode_id": bid, "sku": sku, "code": code, "at": _now()}
        )

    def qr_code(self, *, sku: str, payload: str) -> dict[str, Any]:
        if not payload:
            raise ValidationError("qr payload required")
        qid = _id("wd_qr")
        return self.store.wd_qrcodes.save(
            qid, {"qr_id": qid, "sku": sku, "payload": payload, "at": _now()}
        )

    def rfid(self, *, sku: str, tag_id: str) -> dict[str, Any]:
        if not tag_id:
            raise ValidationError("RFID tag_id required")
        rid = _id("wd_rfid")
        return self.store.wd_rfid.save(
            rid, {"rfid_id": rid, "sku": sku, "tag_id": tag_id, "at": _now()}
        )

    def forecast(self, *, sku: str, days: int = 30, baseline_qty: float = 100.0) -> dict[str, Any]:
        fid = _id("wd_ifcst")
        return self.store.wd_inv_forecasts.save(
            fid,
            {
                "forecast_id": fid,
                "sku": sku,
                "days": int(days),
                "predicted_qty": round(float(baseline_qty) * 1.12, 2),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "items": self.store.wd_inventory.count(),
            "batches": self.store.wd_batches.count(),
            "serials": self.store.wd_serials.count(),
            "forecasts": self.store.wd_inv_forecasts.count(),
        }


class WarehouseAutomation:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def storage_plan(self, *, warehouse_id: str, sku: str, slots: int) -> dict[str, Any]:
        pid = _id("wd_splan")
        return self.store.wd_storage_plans.save(
            pid,
            {
                "plan_id": pid,
                "warehouse_id": warehouse_id,
                "sku": sku,
                "slots": int(slots),
                "at": _now(),
            },
        )

    def optimize_picking(self, *, warehouse_id: str, order_ref: str) -> dict[str, Any]:
        oid = _id("wd_pick")
        return self.store.wd_picking.save(
            oid,
            {
                "optimization_id": oid,
                "warehouse_id": warehouse_id,
                "order_ref": order_ref,
                "path_reduction_pct": 18.0,
                "at": _now(),
            },
        )

    def optimize_packing(self, *, warehouse_id: str, order_ref: str) -> dict[str, Any]:
        oid = _id("wd_pack")
        return self.store.wd_packing.save(
            oid,
            {
                "optimization_id": oid,
                "warehouse_id": warehouse_id,
                "order_ref": order_ref,
                "cube_utilization_pct": 86.0,
                "at": _now(),
            },
        )

    def sort(self, *, warehouse_id: str, lane: str, items: int) -> dict[str, Any]:
        sid = _id("wd_sort")
        return self.store.wd_sorting.save(
            sid,
            {
                "sort_id": sid,
                "warehouse_id": warehouse_id,
                "lane": lane,
                "items": int(items),
                "at": _now(),
            },
        )

    def optimize_loading(self, *, warehouse_id: str, dock_id: str) -> dict[str, Any]:
        oid = _id("wd_lopt")
        return self.store.wd_loading_opts.save(
            oid,
            {
                "optimization_id": oid,
                "warehouse_id": warehouse_id,
                "dock_id": dock_id,
                "fill_rate_pct": 91.0,
                "at": _now(),
            },
        )

    def schedule_dock(self, *, warehouse_id: str, dock_name: str, window_start: str) -> dict[str, Any]:
        if not dock_name:
            raise ValidationError("dock_name required")
        did = _id("wd_dock")
        return self.store.wd_dock_schedules.save(
            did,
            {
                "schedule_id": did,
                "warehouse_id": warehouse_id,
                "dock_name": dock_name,
                "window_start": window_start,
                "at": _now(),
            },
        )

    def assign_agv(self, *, warehouse_id: str, task: str) -> dict[str, Any]:
        aid = _id("wd_agv")
        return self.store.wd_agvs.save(
            aid,
            {
                "agv_id": aid,
                "warehouse_id": warehouse_id,
                "task": task,
                "status": "assigned",
                "at": _now(),
            },
        )

    def assign_robot(self, *, warehouse_id: str, robot_type: str, task: str) -> dict[str, Any]:
        rid = _id("wd_bot")
        return self.store.wd_robots.save(
            rid,
            {
                "robot_id": rid,
                "warehouse_id": warehouse_id,
                "robot_type": robot_type,
                "task": task,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "storage_plans": self.store.wd_storage_plans.count(),
            "picking": self.store.wd_picking.count(),
            "agvs": self.store.wd_agvs.count(),
            "robots": self.store.wd_robots.count(),
        }


class AIWarehouseIntelligence:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def demand_forecast(self, *, sku: str, days: int = 30, baseline: float = 500.0) -> dict[str, Any]:
        fid = _id("wd_admd")
        return self.store.wd_ai_demand.save(
            fid,
            {
                "forecast_id": fid,
                "sku": sku,
                "days": int(days),
                "predicted": round(float(baseline) * 1.09, 2),
                "at": _now(),
            },
        )

    def space_optimize(self, *, warehouse_id: str) -> dict[str, Any]:
        oid = _id("wd_aspc")
        return self.store.wd_ai_space.save(
            oid,
            {
                "optimization_id": oid,
                "warehouse_id": warehouse_id,
                "space_gain_pct": 11.0,
                "at": _now(),
            },
        )

    def inventory_optimize(self, *, warehouse_id: str) -> dict[str, Any]:
        oid = _id("wd_ainv")
        return self.store.wd_ai_inv.save(
            oid,
            {
                "optimization_id": oid,
                "warehouse_id": warehouse_id,
                "stockout_risk_reduction_pct": 14.0,
                "at": _now(),
            },
        )

    def labor_optimize(self, *, warehouse_id: str, headcount: int) -> dict[str, Any]:
        oid = _id("wd_alab")
        return self.store.wd_ai_labor.save(
            oid,
            {
                "optimization_id": oid,
                "warehouse_id": warehouse_id,
                "headcount": int(headcount),
                "productivity_gain_pct": 9.0,
                "at": _now(),
            },
        )

    def energy_optimize(self, *, warehouse_id: str) -> dict[str, Any]:
        oid = _id("wd_aen")
        return self.store.wd_ai_energy.save(
            oid,
            {
                "optimization_id": oid,
                "warehouse_id": warehouse_id,
                "energy_saving_pct": 12.5,
                "at": _now(),
            },
        )

    def cargo_flow_predict(self, *, warehouse_id: str) -> dict[str, Any]:
        pid = _id("wd_aflow")
        return self.store.wd_ai_flow.save(
            pid,
            {
                "prediction_id": pid,
                "warehouse_id": warehouse_id,
                "peak_hour": "14:00",
                "throughput_teu": 420,
                "at": _now(),
            },
        )

    def operational_analytics(self, *, warehouse_id: str) -> dict[str, Any]:
        aid = _id("wd_aops")
        return self.store.wd_ai_ops.save(
            aid,
            {
                "analytics_id": aid,
                "warehouse_id": warehouse_id,
                "otif_pct": 96.2,
                "dwell_hours": 18.5,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "demand_forecasts": self.store.wd_ai_demand.count(),
            "space_opts": self.store.wd_ai_space.count(),
            "ops_analytics": self.store.wd_ai_ops.count(),
        }


class WarehouseDashboard:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str = "warehouse") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "warehouse": {
                "warehouses": self.store.wd_warehouses.count(),
                "zones": self.store.wd_zones.count(),
            },
            "distribution": {
                "dcs": self.store.wd_dcs.count(),
                "fulfillments": self.store.wd_fulfillments.count(),
            },
            "fez": {
                "fezs": self.store.wd_fezs.count(),
                "residents": self.store.wd_residents.count(),
            },
            "inventory": {
                "items": self.store.wd_inventory.count(),
                "batches": self.store.wd_batches.count(),
            },
            "ai_warehouse": {
                "demand": self.store.wd_ai_demand.count(),
                "space": self.store.wd_ai_space.count(),
            },
        }[dashboard_type]
        did = _id("wd_dash")
        return self.store.wd_dashboards.save(
            did,
            {"dashboard_id": did, "dashboard_type": dashboard_type, "metrics": metrics, "generated_at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.wd_dashboards.count(), "types": self.types}


class WarehouseKnowledge:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store
        self.types = list(REGISTRY_TYPES)

    def publish(self, *, registry_type: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if registry_type not in self.types:
            raise ValidationError(f"registry_type must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("wd_reg")
        return self.store.wd_registries.save(
            rid,
            {
                "registry_id": rid,
                "registry_type": registry_type,
                "key": key,
                "payload": payload or {},
                "graph_node": f"wd:{registry_type}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.wd_registries.count(), "types": self.types}
