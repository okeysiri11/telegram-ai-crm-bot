"""Warehouse management and distribution centers."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.port_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store

ZONE_TYPES = ["general", "cold", "hazardous", "bonded", "cross_dock"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class WarehouseManagement:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def register_warehouse(self, *, name: str, capacity_teu: float = 5000.0) -> dict[str, Any]:
        if not name:
            raise ValidationError("warehouse name required")
        wid = _id("wd_wh")
        return self.store.wd_warehouses.save(
            wid,
            {
                "warehouse_id": wid,
                "name": name,
                "capacity_teu": float(capacity_teu),
                "utilized_teu": 0.0,
                "created_at": _now(),
            },
        )

    def create_zone(self, *, warehouse_id: str, name: str, zone_type: str = "general") -> dict[str, Any]:
        if self.store.wd_warehouses.get(warehouse_id) is None:
            raise NotFoundError("warehouse", warehouse_id)
        if zone_type not in ZONE_TYPES:
            raise ValidationError(f"zone_type must be one of {ZONE_TYPES}")
        zid = _id("wd_zone")
        return self.store.wd_zones.save(
            zid,
            {
                "zone_id": zid,
                "warehouse_id": warehouse_id,
                "name": name,
                "zone_type": zone_type,
                "created_at": _now(),
            },
        )

    def receive(self, *, warehouse_id: str, sku: str, qty: float, zone_id: str = "") -> dict[str, Any]:
        if self.store.wd_warehouses.get(warehouse_id) is None:
            raise NotFoundError("warehouse", warehouse_id)
        if not sku:
            raise ValidationError("sku required")
        rid = _id("wd_rcv")
        return self.store.wd_receiving.save(
            rid,
            {
                "receipt_id": rid,
                "warehouse_id": warehouse_id,
                "zone_id": zone_id,
                "sku": sku,
                "qty": float(qty),
                "at": _now(),
            },
        )

    def ship(self, *, warehouse_id: str, sku: str, qty: float) -> dict[str, Any]:
        if self.store.wd_warehouses.get(warehouse_id) is None:
            raise NotFoundError("warehouse", warehouse_id)
        sid = _id("wd_shp")
        return self.store.wd_shipping.save(
            sid,
            {
                "shipment_id": sid,
                "warehouse_id": warehouse_id,
                "sku": sku,
                "qty": float(qty),
                "at": _now(),
            },
        )

    def cross_dock(self, *, warehouse_id: str, inbound_ref: str, outbound_ref: str) -> dict[str, Any]:
        if self.store.wd_warehouses.get(warehouse_id) is None:
            raise NotFoundError("warehouse", warehouse_id)
        cid = _id("wd_xdock")
        return self.store.wd_crossdock.save(
            cid,
            {
                "crossdock_id": cid,
                "warehouse_id": warehouse_id,
                "inbound_ref": inbound_ref,
                "outbound_ref": outbound_ref,
                "at": _now(),
            },
        )

    def cold_storage(self, *, warehouse_id: str, sku: str, temp_c: float = -18.0) -> dict[str, Any]:
        if self.store.wd_warehouses.get(warehouse_id) is None:
            raise NotFoundError("warehouse", warehouse_id)
        cid = _id("wd_cold")
        return self.store.wd_cold.save(
            cid,
            {
                "storage_id": cid,
                "warehouse_id": warehouse_id,
                "sku": sku,
                "temp_c": float(temp_c),
                "at": _now(),
            },
        )

    def hazardous_storage(self, *, warehouse_id: str, sku: str, hazard_class: str) -> dict[str, Any]:
        if self.store.wd_warehouses.get(warehouse_id) is None:
            raise NotFoundError("warehouse", warehouse_id)
        if not hazard_class:
            raise ValidationError("hazard_class required")
        hid = _id("wd_haz")
        return self.store.wd_hazardous.save(
            hid,
            {
                "storage_id": hid,
                "warehouse_id": warehouse_id,
                "sku": sku,
                "hazard_class": hazard_class,
                "at": _now(),
            },
        )

    def optimize_inventory(self, *, warehouse_id: str) -> dict[str, Any]:
        if self.store.wd_warehouses.get(warehouse_id) is None:
            raise NotFoundError("warehouse", warehouse_id)
        oid = _id("wd_iopt")
        return self.store.wd_inv_opts.save(
            oid,
            {
                "optimization_id": oid,
                "warehouse_id": warehouse_id,
                "space_gain_pct": 8.5,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "warehouses": self.store.wd_warehouses.count(),
            "zones": self.store.wd_zones.count(),
            "receipts": self.store.wd_receiving.count(),
            "shipments": self.store.wd_shipping.count(),
        }


class DistributionCenters:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def register_dc(self, *, name: str, region: str = "", capacity_teu: float = 10000.0) -> dict[str, Any]:
        if not name:
            raise ValidationError("distribution center name required")
        did = _id("wd_dc")
        return self.store.wd_dcs.save(
            did,
            {
                "dc_id": did,
                "name": name,
                "region": region,
                "capacity_teu": float(capacity_teu),
                "created_at": _now(),
            },
        )

    def register_hub(self, *, name: str, region: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("hub name required")
        hid = _id("wd_hub")
        return self.store.wd_hubs.save(
            hid, {"hub_id": hid, "name": name, "region": region, "created_at": _now()}
        )

    def consolidate(self, *, dc_id: str, order_refs: list[str]) -> dict[str, Any]:
        if self.store.wd_dcs.get(dc_id) is None:
            raise NotFoundError("distribution_center", dc_id)
        if not order_refs:
            raise ValidationError("order_refs required")
        cid = _id("wd_cons")
        return self.store.wd_consolidations.save(
            cid,
            {
                "consolidation_id": cid,
                "dc_id": dc_id,
                "order_refs": order_refs,
                "at": _now(),
            },
        )

    def fulfill(self, *, dc_id: str, order_ref: str) -> dict[str, Any]:
        if self.store.wd_dcs.get(dc_id) is None:
            raise NotFoundError("distribution_center", dc_id)
        fid = _id("wd_ful")
        return self.store.wd_fulfillments.save(
            fid,
            {
                "fulfillment_id": fid,
                "dc_id": dc_id,
                "order_ref": order_ref,
                "status": "fulfilled",
                "at": _now(),
            },
        )

    def allocate(self, *, dc_id: str, sku: str, qty: float) -> dict[str, Any]:
        if self.store.wd_dcs.get(dc_id) is None:
            raise NotFoundError("distribution_center", dc_id)
        aid = _id("wd_alloc")
        return self.store.wd_allocations.save(
            aid,
            {
                "allocation_id": aid,
                "dc_id": dc_id,
                "sku": sku,
                "qty": float(qty),
                "at": _now(),
            },
        )

    def load_plan(self, *, dc_id: str, vehicle_ref: str, teu: float) -> dict[str, Any]:
        if self.store.wd_dcs.get(dc_id) is None:
            raise NotFoundError("distribution_center", dc_id)
        lid = _id("wd_load")
        return self.store.wd_load_plans.save(
            lid,
            {
                "plan_id": lid,
                "dc_id": dc_id,
                "vehicle_ref": vehicle_ref,
                "teu": float(teu),
                "at": _now(),
            },
        )

    def dispatch(self, *, dc_id: str, destination: str, vehicle_ref: str = "") -> dict[str, Any]:
        if self.store.wd_dcs.get(dc_id) is None:
            raise NotFoundError("distribution_center", dc_id)
        did = _id("wd_disp")
        return self.store.wd_dispatches.save(
            did,
            {
                "dispatch_id": did,
                "dc_id": dc_id,
                "destination": destination,
                "vehicle_ref": vehicle_ref,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "distribution_centers": self.store.wd_dcs.count(),
            "hubs": self.store.wd_hubs.count(),
            "fulfillments": self.store.wd_fulfillments.count(),
            "dispatches": self.store.wd_dispatches.count(),
        }


class FreeEconomicZones:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def register_fez(self, *, name: str, region: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("FEZ name required")
        fid = _id("wd_fez")
        return self.store.wd_fezs.save(
            fid, {"fez_id": fid, "name": name, "region": region, "created_at": _now()}
        )

    def register_resident(self, *, fez_id: str, company_name: str) -> dict[str, Any]:
        if self.store.wd_fezs.get(fez_id) is None:
            raise NotFoundError("fez", fez_id)
        if not company_name:
            raise ValidationError("company_name required")
        rid = _id("wd_res")
        return self.store.wd_residents.save(
            rid,
            {
                "resident_id": rid,
                "fez_id": fez_id,
                "company_name": company_name,
                "created_at": _now(),
            },
        )

    def tax_benefit(self, *, fez_id: str, benefit_type: str, rate_pct: float) -> dict[str, Any]:
        if self.store.wd_fezs.get(fez_id) is None:
            raise NotFoundError("fez", fez_id)
        tid = _id("wd_tax")
        return self.store.wd_tax_benefits.save(
            tid,
            {
                "benefit_id": tid,
                "fez_id": fez_id,
                "benefit_type": benefit_type,
                "rate_pct": float(rate_pct),
                "at": _now(),
            },
        )

    def duty_free(self, *, fez_id: str, operation_ref: str, value: float) -> dict[str, Any]:
        if self.store.wd_fezs.get(fez_id) is None:
            raise NotFoundError("fez", fez_id)
        did = _id("wd_dfree")
        return self.store.wd_duty_free.save(
            did,
            {
                "operation_id": did,
                "fez_id": fez_id,
                "operation_ref": operation_ref,
                "value": float(value),
                "at": _now(),
            },
        )

    def bonded_warehouse(self, *, fez_id: str, name: str, capacity_teu: float = 2000.0) -> dict[str, Any]:
        if self.store.wd_fezs.get(fez_id) is None:
            raise NotFoundError("fez", fez_id)
        bid = _id("wd_bond")
        return self.store.wd_bonded.save(
            bid,
            {
                "bonded_id": bid,
                "fez_id": fez_id,
                "name": name,
                "capacity_teu": float(capacity_teu),
                "created_at": _now(),
            },
        )

    def customs_link(self, *, fez_id: str, customs_office_ref: str) -> dict[str, Any]:
        if self.store.wd_fezs.get(fez_id) is None:
            raise NotFoundError("fez", fez_id)
        cid = _id("wd_clink")
        return self.store.wd_customs_links.save(
            cid,
            {
                "link_id": cid,
                "fez_id": fez_id,
                "customs_office_ref": customs_office_ref,
                "at": _now(),
            },
        )

    def compliance_monitor(self, *, fez_id: str, status: str = "compliant") -> dict[str, Any]:
        if self.store.wd_fezs.get(fez_id) is None:
            raise NotFoundError("fez", fez_id)
        mid = _id("wd_fcmp")
        return self.store.wd_fez_compliance.save(
            mid,
            {
                "monitor_id": mid,
                "fez_id": fez_id,
                "status": status,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "fezs": self.store.wd_fezs.count(),
            "residents": self.store.wd_residents.count(),
            "bonded": self.store.wd_bonded.count(),
            "duty_free_ops": self.store.wd_duty_free.count(),
        }
