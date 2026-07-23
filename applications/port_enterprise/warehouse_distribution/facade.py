"""Warehouse, FEZ & Distribution facade — Sprint 15.5."""

from __future__ import annotations

from typing import Any

from applications.port_enterprise.config import DEFAULT_CONFIG
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store
from applications.port_enterprise.warehouse_distribution.services import (
    AIWarehouseIntelligence,
    InventoryIntelligence,
    WarehouseAutomation,
    WarehouseDashboard,
    WarehouseKnowledge,
)
from applications.port_enterprise.warehouse_distribution.warehouse import (
    DistributionCenters,
    FreeEconomicZones,
    WarehouseManagement,
)


class WarehouseDistributionSuite:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store
        self.warehouse = WarehouseManagement(self.store)
        self.distribution = DistributionCenters(self.store)
        self.fez = FreeEconomicZones(self.store)
        self.inventory = InventoryIntelligence(self.store)
        self.automation = WarehouseAutomation(self.store)
        self.ai = AIWarehouseIntelligence(self.store)
        self.dashboard = WarehouseDashboard(self.store)
        self.knowledge = WarehouseKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        wh = self.warehouse.register_warehouse(name="Port CFS Warehouse", capacity_teu=8000)
        zone = self.warehouse.create_zone(warehouse_id=wh["warehouse_id"], name="Zone A", zone_type="general")
        self.warehouse.create_zone(warehouse_id=wh["warehouse_id"], name="Cold A", zone_type="cold")
        self.warehouse.create_zone(warehouse_id=wh["warehouse_id"], name="Hazmat", zone_type="hazardous")
        self.warehouse.receive(warehouse_id=wh["warehouse_id"], sku="SKU-100", qty=200, zone_id=zone["zone_id"])
        self.warehouse.ship(warehouse_id=wh["warehouse_id"], sku="SKU-100", qty=40)
        self.warehouse.cross_dock(warehouse_id=wh["warehouse_id"], inbound_ref="IN-1", outbound_ref="OUT-1")
        self.warehouse.cold_storage(warehouse_id=wh["warehouse_id"], sku="SKU-REEFER", temp_c=-20)
        self.warehouse.hazardous_storage(warehouse_id=wh["warehouse_id"], sku="SKU-HAZ", hazard_class="3")
        inv_opt = self.warehouse.optimize_inventory(warehouse_id=wh["warehouse_id"])

        dc = self.distribution.register_dc(name="Central DC", region="South", capacity_teu=15000)
        self.distribution.register_hub(name="Regional Hub East", region="East")
        self.distribution.consolidate(dc_id=dc["dc_id"], order_refs=["ORD-1", "ORD-2"])
        ful = self.distribution.fulfill(dc_id=dc["dc_id"], order_ref="ORD-1")
        self.distribution.allocate(dc_id=dc["dc_id"], sku="SKU-100", qty=50)
        self.distribution.load_plan(dc_id=dc["dc_id"], vehicle_ref="TRK-9", teu=2.0)
        disp = self.distribution.dispatch(dc_id=dc["dc_id"], destination="Lviv", vehicle_ref="TRK-9")

        fez = self.fez.register_fez(name="Odessa FEZ", region="UA")
        res = self.fez.register_resident(fez_id=fez["fez_id"], company_name="Port Free Trade LLC")
        self.fez.tax_benefit(fez_id=fez["fez_id"], benefit_type="corporate_tax", rate_pct=50)
        self.fez.duty_free(fez_id=fez["fez_id"], operation_ref="DF-001", value=250000)
        bonded = self.fez.bonded_warehouse(fez_id=fez["fez_id"], name="Bonded WH-1", capacity_teu=3000)
        self.fez.customs_link(fez_id=fez["fez_id"], customs_office_ref="UAODS")
        self.fez.compliance_monitor(fez_id=fez["fez_id"], status="compliant")

        inv = self.inventory.upsert_item(warehouse_id=wh["warehouse_id"], sku="SKU-100", qty=160)
        self.inventory.track_batch(sku="SKU-100", batch_no="B-2026-01", qty=160)
        self.inventory.track_lot(sku="SKU-100", lot_no="L-55", qty=160)
        self.inventory.track_serial(sku="SKU-100", serial_no="SN-9001")
        self.inventory.barcode(sku="SKU-100", code="5901234123457")
        self.inventory.qr_code(sku="SKU-100", payload="sku:SKU-100")
        self.inventory.rfid(sku="SKU-100", tag_id="RFID-7788")
        forecast = self.inventory.forecast(sku="SKU-100", days=30, baseline_qty=160)

        self.automation.storage_plan(warehouse_id=wh["warehouse_id"], sku="SKU-100", slots=24)
        pick = self.automation.optimize_picking(warehouse_id=wh["warehouse_id"], order_ref="ORD-1")
        self.automation.optimize_packing(warehouse_id=wh["warehouse_id"], order_ref="ORD-1")
        self.automation.sort(warehouse_id=wh["warehouse_id"], lane="L1", items=80)
        self.automation.optimize_loading(warehouse_id=wh["warehouse_id"], dock_id="D1")
        self.automation.schedule_dock(
            warehouse_id=wh["warehouse_id"], dock_name="Dock 1", window_start="2026-08-20T08:00:00Z"
        )
        agv = self.automation.assign_agv(warehouse_id=wh["warehouse_id"], task="move_pallet")
        self.automation.assign_robot(warehouse_id=wh["warehouse_id"], robot_type="picker", task="pick")

        demand = self.ai.demand_forecast(sku="SKU-100", days=30, baseline=500)
        self.ai.space_optimize(warehouse_id=wh["warehouse_id"])
        self.ai.inventory_optimize(warehouse_id=wh["warehouse_id"])
        self.ai.labor_optimize(warehouse_id=wh["warehouse_id"], headcount=40)
        self.ai.energy_optimize(warehouse_id=wh["warehouse_id"])
        self.ai.cargo_flow_predict(warehouse_id=wh["warehouse_id"])
        ops = self.ai.operational_analytics(warehouse_id=wh["warehouse_id"])

        for rtype, key in (
            ("warehouse", wh["warehouse_id"]),
            ("distribution", dc["dc_id"]),
            ("fez", fez["fez_id"]),
            ("inventory", inv["inventory_id"]),
            ("automation", agv["agv_id"]),
        ):
            self.knowledge.publish(registry_type=rtype, key=key, payload={"bootstrap": True})

        dash = self.dashboard.render(dashboard_type="warehouse")
        return {
            "bootstrap": True,
            "warehouse_id": wh["warehouse_id"],
            "zone_id": zone["zone_id"],
            "inventory_opt_id": inv_opt["optimization_id"],
            "dc_id": dc["dc_id"],
            "fulfillment_id": ful["fulfillment_id"],
            "dispatch_id": disp["dispatch_id"],
            "fez_id": fez["fez_id"],
            "resident_id": res["resident_id"],
            "bonded_id": bonded["bonded_id"],
            "inventory_id": inv["inventory_id"],
            "forecast_id": forecast["forecast_id"],
            "picking_id": pick["optimization_id"],
            "agv_id": agv["agv_id"],
            "demand_id": demand["forecast_id"],
            "ops_id": ops["analytics_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "warehouse": self.warehouse.status(),
            "distribution": self.distribution.status(),
            "fez": self.fez.status(),
            "inventory": self.inventory.status(),
            "automation": self.automation.status(),
            "ai": self.ai.status(),
            "dashboard": self.dashboard.status(),
            "knowledge": self.knowledge.status(),
        }


warehouse_distribution = WarehouseDistributionSuite()
