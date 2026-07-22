"""Mobility Platform Suite facade — Sprint 13.8."""

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.config import DEFAULT_CONFIG
from applications.auto_marketplace.mobility_platform.ev_maas import EVEcosystem, MaaSPlatform
from applications.auto_marketplace.mobility_platform.hub import MobilityHub
from applications.auto_marketplace.mobility_platform.services import (
    AIMobility,
    LogisticsIntelligence,
    MobilityDashboard,
    MobilityKnowledge,
    SmartCity,
    SmartTransportation,
)
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class MobilityPlatformSuite:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.hub = MobilityHub(self.store)
        self.ev = EVEcosystem(self.store)
        self.maas = MaaSPlatform(self.store)
        self.transport = SmartTransportation(self.store)
        self.logistics = LogisticsIntelligence(self.store)
        self.ai = AIMobility(self.store)
        self.smart_city = SmartCity(self.store)
        self.dashboard = MobilityDashboard(self.store)
        self.knowledge = MobilityKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        hub = self.hub.create_hub(name="Central Mobility Hub", region="EU-Central", city="Berlin")
        self.hub.add_network_node(hub_id=hub["hub_id"], node_type="station", name="Hauptbahnhof", lat=52.525, lon=13.369)
        self.hub.register_region(name="Berlin Metro", manager="CityOps")
        plan = self.hub.travel_plan(origin="Mitte", destination="Potsdam", preferences={"mode": "drive"})
        opt = self.hub.optimize_trip(plan_id=plan["plan_id"])
        self.hub.traffic_snapshot(region="Berlin", congestion=0.55)

        ev = self.ev.register_ev(vin="WVWZZZ1JZXW000001", model="ID.4", battery_kwh=77)
        self.ev.battery_health(ev["ev_id"], soh_pct=91, cycles=340)
        charger = self.ev.register_charger(name="ChargePoint Mitte", lat=52.52, lon=13.4, kw=150)
        session = self.ev.start_session(ev_id=ev["ev_id"], charger_id=charger["charger_id"], kwh_target=30)
        session = self.ev.end_session(session["session_id"], kwh_delivered=28.5)
        rang = self.ev.range_prediction(ev_id=ev["ev_id"], soc_pct=75, temp_c=18)
        self.ev.charging_route(ev_id=ev["ev_id"], origin="Berlin", destination="Hamburg")
        self.ev.energy_analytics(ev["ev_id"])

        offering = self.maas.create_offering(name="City Share EV", service_type="car_share", region="Berlin")
        self.maas.create_offering(name="Corp Fleet Desk", service_type="corporate", region="Berlin")
        self.maas.create_offering(name="RideNow", service_type="ride_share", region="Berlin")
        reservation = self.maas.reserve(
            offering_id=offering["offering_id"],
            user="alex@example.com",
            starts_at="2026-07-25T09:00:00Z",
            ends_at="2026-07-25T18:00:00Z",
        )

        self.transport.traffic_flow(corridor="A100", vehicles_per_hour=1600)
        self.transport.congestion_prediction(region="Berlin", horizon_min=45)
        self.transport.road_condition(road_id="B1", condition="wet")
        self.transport.parking_availability(zone="Mitte", available=42, capacity=120)
        self.transport.public_transport(line="U2", mode="metro", headway_min=4)
        self.transport.emergency_route(origin="Accident-A100", destination="Charite")

        ship = self.logistics.create_shipment(cargo="Parts pallet", origin="Warehouse-N", destination="Dealer-S")
        self.logistics.optimize_delivery(shipment_id=ship["shipment_id"], stops=["Hub-1", "Dealer-S"])
        self.logistics.track_cargo(shipment_id=ship["shipment_id"], lat=52.5, lon=13.4)
        self.logistics.dispatch(vehicle_id="fleet_van_1", shipment_id=ship["shipment_id"])
        self.logistics.warehouse_link(warehouse="WH-Berlin", shipment_id=ship["shipment_id"])

        self.ai.demand_forecast(region="Berlin", horizon_h=24)
        self.ai.recommend(user="alex@example.com", intent="commute")
        self.ai.travel_time(origin="Mitte", destination="Potsdam")
        self.ai.energy_optimize(ev_id=ev["ev_id"], route_km=35)
        carbon = self.ai.carbon_footprint(trips=3, mode="ev")

        self.smart_city.register_asset(kind="road_sensor", name="Sensor A100-12")
        self.smart_city.register_asset(kind="traffic_control", name="Signal Mitte-1")
        self.smart_city.register_asset(kind="weather", name="Berlin Weather Feed")
        self.smart_city.register_asset(kind="emergency", name="City EMS")
        urban = self.smart_city.urban_dashboard(city="Berlin")

        for rtype, key in (
            ("mobility", hub["hub_id"]),
            ("transportation", "Berlin"),
            ("ev", ev["ev_id"]),
            ("infrastructure", "Berlin"),
            ("logistics", ship["shipment_id"]),
        ):
            self.knowledge.publish(registry_type=rtype, key=key, payload={"bootstrap": True})

        dash = self.dashboard.render(dashboard_type="mobility")
        return {
            "bootstrap": True,
            "hub_id": hub["hub_id"],
            "plan_id": plan["plan_id"],
            "optimization_id": opt["optimization_id"],
            "ev_id": ev["ev_id"],
            "charger_id": charger["charger_id"],
            "session_id": session["session_id"],
            "range_id": rang["range_id"],
            "reservation_id": reservation["reservation_id"],
            "shipment_id": ship["shipment_id"],
            "carbon_id": carbon["footprint_id"],
            "urban_dashboard_id": urban["dashboard_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "hub": self.hub.status(),
            "ev": self.ev.status(),
            "maas": self.maas.status(),
            "transport": self.transport.status(),
            "logistics": self.logistics.status(),
            "ai": self.ai.status(),
            "smart_city": self.smart_city.status(),
            "dashboard": self.dashboard.status(),
            "knowledge": self.knowledge.status(),
        }


mobility_platform = MobilityPlatformSuite()
