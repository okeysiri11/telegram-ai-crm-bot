"""Multimodal Logistics Suite facade — Sprint 15.3."""

from __future__ import annotations

from typing import Any

from applications.port_enterprise.config import DEFAULT_CONFIG
from applications.port_enterprise.multimodal_logistics.rail_truck import RailLogistics, TruckLogistics
from applications.port_enterprise.multimodal_logistics.services import MultimodalDashboard, MultimodalKnowledge
from applications.port_enterprise.multimodal_logistics.transport import (
    AILogisticsIntelligence,
    InlandLogistics,
    MultimodalTransport,
    ShipmentManagement,
)
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store


class MultimodalLogisticsSuite:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store
        self.rail = RailLogistics(self.store)
        self.truck = TruckLogistics(self.store)
        self.multimodal = MultimodalTransport(self.store)
        self.inland = InlandLogistics(self.store)
        self.shipments = ShipmentManagement(self.store)
        self.ai = AILogisticsIntelligence(self.store)
        self.dashboard = MultimodalDashboard(self.store)
        self.knowledge = MultimodalKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        network = self.rail.register_network(name="Black Sea Rail Corridor", region="UA-EU")
        rterm = self.rail.register_terminal(name="Odessa Rail Terminal", network_id=network["network_id"])
        train = self.rail.register_train(name="ODS-KYIV-01", terminal_id=rterm["terminal_id"])
        self.rail.register_wagon(code="WAG-1001", train_id=train["train_id"], capacity_teu=2)
        self.rail.register_locomotive(name="LOC-4400", power_kw=4400)
        self.rail.schedule(
            train_id=train["train_id"],
            origin="Odessa",
            destination="Kyiv",
            departs_at="2026-08-15T18:00:00Z",
        )
        self.rail.track_cargo(train_id=train["train_id"], cargo_ref="CTR-AA", status="loaded")
        self.rail.capacity_plan(network_id=network["network_id"], teu=12000, horizon_days=30)

        truck = self.truck.register_truck(plate="AA9999BB", capacity_t=24)
        self.truck.register_trailer(code="TRL-55", truck_id=truck["truck_id"])
        driver = self.truck.register_driver(name="Ivan Driver", license_no="DRV-7788")
        self.truck.dispatch(truck_id=truck["truck_id"], driver_id=driver["driver_id"], destination="Dry Port Lviv")
        self.truck.plan_route(truck_id=truck["truck_id"], origin="Odessa", destination="Lviv")
        self.truck.track(truck_id=truck["truck_id"], lat=46.5, lon=30.7)
        self.truck.fuel(truck["truck_id"], liters=380)
        self.truck.maintain(truck["truck_id"], work="tires", due_at="2026-09-01")

        chain = self.multimodal.create_chain(
            name="Sea-Rail-Truck Corridor",
            legs=[
                {"mode": "sea", "from": "Istanbul", "to": "Odessa"},
                {"mode": "rail", "from": "Odessa", "to": "Lviv"},
                {"mode": "truck", "from": "Lviv", "to": "Warehouse"},
            ],
        )
        self.multimodal.mode_transfer(
            chain_id=chain["chain_id"], from_mode="sea", to_mode="rail", location="Odessa Port"
        )
        self.multimodal.container_transfer(
            chain_id=chain["chain_id"], container_ref="MSCU1234567", location="Rail Terminal"
        )
        imt = self.multimodal.intermodal_terminal(name="Lviv Intermodal", modes=["rail", "truck"])
        self.multimodal.cross_dock(terminal_id=imt["terminal_id"], inbound="train", outbound="truck")
        self.multimodal.consolidate(shipment_refs=["SHP-1", "SHP-2"], destination="Warehouse")
        self.multimodal.optimize_transport(chain_id=chain["chain_id"])

        dry = self.inland.register_dry_port(name="Lviv Dry Port", region="West UA")
        self.inland.register_dc(name="Central DC", capacity_teu=8000)
        self.inland.register_hub(name="Regional Hub West")
        self.inland.redistribute(from_site=dry["dry_port_id"], to_site="Central DC", teu=120)
        self.inland.coordinate_storage(site=dry["dry_port_id"], teu=450)

        shp = self.shipments.register(reference="SHP-BOOT-001", origin="Odessa", destination="Warsaw")
        self.shipments.track(shp["shipment_id"], status="in_transit", location="Rail")
        self.shipments.document(shp["shipment_id"], doc_type="cmr", title="CMR Note")
        self.shipments.eta(shp["shipment_id"], hours=36)
        self.shipments.schedule_delivery(
            shp["shipment_id"], window_start="2026-08-18T08:00:00Z", window_end="2026-08-18T18:00:00Z"
        )
        pod = self.shipments.proof_of_delivery(shp["shipment_id"], signed_by="Receiver Co")

        demand = self.ai.demand_forecast(corridor="Odessa-Lviv", teu=5000, days=30)
        route = self.ai.optimize_route(origin="Odessa", destination="Lviv", mode="rail")
        self.ai.optimize_fleet(fleet_size=40)
        self.ai.traffic_prediction(corridor="Odessa-Lviv")
        self.ai.capacity_forecast(node="Lviv Dry Port", teu=3000)
        self.ai.cost_optimize(shipment_id=shp["shipment_id"], baseline_cost=2400)
        self.ai.delay_predict(shipment_id=shp["shipment_id"], risk=0.25)
        carbon = self.ai.carbon_analytics(shipment_id=shp["shipment_id"], ton_km=18000)

        for rtype, key in (
            ("logistics", chain["chain_id"]),
            ("rail", train["train_id"]),
            ("truck", truck["truck_id"]),
            ("shipment", shp["shipment_id"]),
            ("multimodal", imt["terminal_id"]),
        ):
            self.knowledge.publish(registry_type=rtype, key=key, payload={"bootstrap": True})

        dash = self.dashboard.render(dashboard_type="multimodal")
        return {
            "bootstrap": True,
            "network_id": network["network_id"],
            "train_id": train["train_id"],
            "truck_id": truck["truck_id"],
            "driver_id": driver["driver_id"],
            "chain_id": chain["chain_id"],
            "dry_port_id": dry["dry_port_id"],
            "shipment_id": shp["shipment_id"],
            "pod_id": pod["pod_id"],
            "demand_forecast_id": demand["forecast_id"],
            "route_id": route["route_id"],
            "carbon_id": carbon["analytics_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "rail": self.rail.status(),
            "truck": self.truck.status(),
            "multimodal": self.multimodal.status(),
            "inland": self.inland.status(),
            "shipments": self.shipments.status(),
            "ai": self.ai.status(),
            "dashboard": self.dashboard.status(),
            "knowledge": self.knowledge.status(),
        }


multimodal_logistics = MultimodalLogisticsSuite()
