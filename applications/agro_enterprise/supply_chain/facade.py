"""Supply Chain Suite facade — Sprint 14.5."""

from __future__ import annotations

from typing import Any

from applications.agro_enterprise.config import DEFAULT_CONFIG
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store
from applications.agro_enterprise.supply_chain.services import SupplyChainDashboard, SupplyChainKnowledge
from applications.agro_enterprise.supply_chain.supply import (
    GrainElevatorManagement,
    GrainQualityIntelligence,
    SupplyChainManagement,
)
from applications.agro_enterprise.supply_chain.warehouse import (
    AgroLogistics,
    ExportTrading,
    ProcessingManagement,
    WarehouseManagement,
)


class SupplyChainSuite:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.supply = SupplyChainManagement(self.store)
        self.elevator = GrainElevatorManagement(self.store)
        self.quality = GrainQualityIntelligence(self.store)
        self.warehouse = WarehouseManagement(self.store)
        self.processing = ProcessingManagement(self.store)
        self.logistics = AgroLogistics(self.store)
        self.export = ExportTrading(self.store)
        self.dashboard = SupplyChainDashboard(self.store)
        self.knowledge = SupplyChainKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        node = self.supply.add_node(name="Black Sea Hub", node_type="port", region="UA")
        dc = self.supply.add_distribution_center(name="Central DC", capacity_t=50000)
        ship = self.supply.track_shipment(origin="Elevator A", destination="Port Odessa", commodity="wheat", tons=2000)
        self.supply.supply_plan(commodity="wheat", tons=80000, horizon_days=60)
        self.supply.demand_plan(commodity="wheat", tons=75000, market="MENA")
        order = self.supply.create_order(buyer="Grain Traders Ltd", commodity="wheat", tons=5000, price=245)

        elev = self.elevator.register_elevator(name="Elevator A", location="Poltava")
        silo = self.elevator.register_silo(elevator_id=elev["elevator_id"], capacity_t=10000, commodity="wheat")
        self.elevator.intake(silo["silo_id"], tons=3500)
        self.elevator.dry(silo["silo_id"], target_moisture_pct=13.5)
        self.elevator.clean(silo["silo_id"])
        self.elevator.monitor(silo["silo_id"], temp_c=17.5, humidity_pct=52, aeration=True)
        self.elevator.dispatch(silo["silo_id"], tons=500)

        insp = self.quality.inspect(
            lot_id="LOT-WHEAT-001", moisture_pct=13.2, protein_pct=12.8, foreign_material_pct=0.8
        )
        cert = self.quality.certificate(insp["inspection_id"])

        wh = self.warehouse.register_warehouse(name="Port Warehouse 1", cold_storage=False)
        inv = self.warehouse.add_inventory(
            warehouse_id=wh["warehouse_id"], sku="WHEAT-A", tons=1200, lot="LOT-WHEAT-001"
        )
        self.warehouse.optimize(wh["warehouse_id"])

        plant = self.processing.register_plant(name="Clean & Dry Plant", capacity_t_day=800)
        self.processing.run_operation(plant_id=plant["plant_id"], operation="cleaning", tons=400)
        self.processing.run_operation(plant_id=plant["plant_id"], operation="drying", tons=400)
        self.processing.production_plan(plant_id=plant["plant_id"], commodity="wheat", tons=5000)

        truck = self.logistics.register_truck(plate="AA1234BB", capacity_t=25)
        self.logistics.register_rail(wagon="R-9001", capacity_t=60)
        self.logistics.register_container(code="MSCU1234567", teu=1)
        route = self.logistics.optimize_route(origin="Poltava", destination="Odessa", mode="truck")
        self.logistics.freight_plan(commodity="wheat", tons=2000, mode="truck")
        self.logistics.track_cargo(shipment_ref=ship["shipment_id"], lat=46.48, lon=30.73)
        self.logistics.schedule_delivery(
            shipment_ref=ship["shipment_id"], window_start="2026-08-01T08:00:00Z", window_end="2026-08-01T18:00:00Z"
        )

        buyer = self.export.register_buyer(name="Cairo Mills", country="EG")
        contract = self.export.create_contract(
            buyer=buyer["name"], commodity="wheat", tons=10000, price=255, incoterm="FOB"
        )
        self.export.price_quote(commodity="wheat", market="CBOT")
        docs = self.export.export_docs(contract_id=contract["contract_id"])
        desk = self.export.trading_desk_order(side="sell", commodity="wheat", tons=2000, price=250)

        for rtype, key in (
            ("supply_chain", node["node_id"]),
            ("warehouse", wh["warehouse_id"]),
            ("elevator", elev["elevator_id"]),
            ("quality", insp["inspection_id"]),
            ("export", contract["contract_id"]),
        ):
            self.knowledge.publish(registry_type=rtype, key=key, payload={"bootstrap": True})

        dash = self.dashboard.render(dashboard_type="supply_chain")
        return {
            "bootstrap": True,
            "node_id": node["node_id"],
            "dc_id": dc["dc_id"],
            "shipment_id": ship["shipment_id"],
            "order_id": order["order_id"],
            "elevator_id": elev["elevator_id"],
            "silo_id": silo["silo_id"],
            "inspection_id": insp["inspection_id"],
            "certificate_id": cert["certificate_id"],
            "warehouse_id": wh["warehouse_id"],
            "inventory_id": inv["inventory_id"],
            "plant_id": plant["plant_id"],
            "truck_id": truck["truck_id"],
            "route_id": route["route_id"],
            "contract_id": contract["contract_id"],
            "doc_pack_id": docs["doc_pack_id"],
            "desk_order_id": desk["desk_order_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "supply": self.supply.status(),
            "elevator": self.elevator.status(),
            "quality": self.quality.status(),
            "warehouse": self.warehouse.status(),
            "processing": self.processing.status(),
            "logistics": self.logistics.status(),
            "export": self.export.status(),
            "dashboard": self.dashboard.status(),
            "knowledge": self.knowledge.status(),
        }


supply_chain = SupplyChainSuite()
