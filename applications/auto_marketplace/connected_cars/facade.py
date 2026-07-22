"""Connected Cars Suite facade — Sprint 13.7."""

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.config import DEFAULT_CONFIG
from applications.auto_marketplace.connected_cars.core import ConnectedCarsCore
from applications.auto_marketplace.connected_cars.remote import PredictiveAI, RemoteVehicleManagement
from applications.auto_marketplace.connected_cars.services import (
    ExecutiveDashboard,
    FleetIntelligence,
    KnowledgeRegistry,
    SmartServices,
)
from applications.auto_marketplace.connected_cars.telematics import Telematics
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class ConnectedCarsSuite:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.core = ConnectedCarsCore(self.store)
        self.telematics = Telematics(self.store)
        self.remote = RemoteVehicleManagement(self.store)
        self.predictive = PredictiveAI(self.store)
        self.fleet = FleetIntelligence(self.store)
        self.smart = SmartServices(self.store)
        self.dashboard = ExecutiveDashboard(self.store)
        self.knowledge = KnowledgeRegistry(self.store)

    def bootstrap(self) -> dict[str, Any]:
        vehicle = self.core.register_vehicle(vin="1HGCM82633A000001", label="Connected-01", fleet_id="fleet_eu")
        hub = self.core.connect_vehicle(vehicle["connected_vehicle_id"], protocol="mqtt")
        obd = self.core.register_iot_device(connected_vehicle_id=vehicle["connected_vehicle_id"], kind="obd", serial="OBD-100")
        self.core.register_iot_device(connected_vehicle_id=vehicle["connected_vehicle_id"], kind="edge", serial="EDGE-1")
        self.core.register_iot_device(connected_vehicle_id=vehicle["connected_vehicle_id"], kind="gateway", serial="GW-1")
        self.core.send_message(connected_vehicle_id=vehicle["connected_vehicle_id"], channel="telematics", payload={"hello": True})

        self.telematics.track_gps(connected_vehicle_id=vehicle["connected_vehicle_id"], lat=52.52, lon=13.405, speed_kmh=48)
        trip = self.telematics.start_trip(connected_vehicle_id=vehicle["connected_vehicle_id"], origin="Berlin")
        trip = self.telematics.end_trip(trip["trip_id"], destination="Potsdam", distance_km=35, fuel_liters=2.8, harsh_events=1)
        self.telematics.monitor_fuel(connected_vehicle_id=vehicle["connected_vehicle_id"], level_pct=62, liters=28)
        self.telematics.monitor_battery(connected_vehicle_id=vehicle["connected_vehicle_id"], soc_pct=88, voltage=12.6)
        self.telematics.obd_snapshot(connected_vehicle_id=vehicle["connected_vehicle_id"], codes=[], rpm=2100, coolant=91)
        self.telematics.record_event(connected_vehicle_id=vehicle["connected_vehicle_id"], event_type="ignition_on", severity="info")

        health = self.remote.health(vehicle["connected_vehicle_id"])
        diag = self.remote.remote_diagnostics(vehicle["connected_vehicle_id"])
        self.remote.notify(connected_vehicle_id=vehicle["connected_vehicle_id"], title="Trip complete", body="35 km")
        self.remote.command(connected_vehicle_id=vehicle["connected_vehicle_id"], command="locate")
        self.remote.maintenance_alert(connected_vehicle_id=vehicle["connected_vehicle_id"], message="Oil interval soon", due_at="2026-08-15")
        self.remote.register_firmware(connected_vehicle_id=vehicle["connected_vehicle_id"], component="tcu", version="2.4.1")

        pred = self.predictive.predict(
            connected_vehicle_id=vehicle["connected_vehicle_id"],
            mileage=72000,
            battery_soc=88,
            engine_load=0.45,
            brake_km=28000,
            tire_km=31000,
            utilization=0.62,
        )
        fleet_dash = self.fleet.dashboard(fleet_id="fleet_eu")
        self.smart.register(kind="charging", name="Berlin Charge Hub", lat=52.52, lon=13.4)
        self.smart.register(kind="fuel", name="Shell Mitte", lat=52.51, lon=13.39)
        self.smart.register(kind="service_center", name="Prime Motors Service", lat=52.5, lon=13.41)
        self.smart.register(kind="roadside", name="EU Assist", lat=52.53, lon=13.42)
        self.smart.register(kind="insurance", name="Connected Cover", meta={"policy": "telematics"})
        self.smart.register(kind="parking", name="Potsdamer Platz P1", lat=52.509, lon=13.376)

        for rtype, key in (
            ("telemetry", vehicle["vin"]),
            ("fleet", "fleet_eu"),
            ("iot", obd["device_id"]),
            ("diagnostics", diag["diagnostics_id"]),
            ("predictive", pred["prediction_id"]),
        ):
            self.knowledge.publish(registry_type=rtype, key=key, payload={"bootstrap": True})

        exec_dash = self.dashboard.render(dashboard_type="connected_fleet")
        return {
            "bootstrap": True,
            "connected_vehicle_id": vehicle["connected_vehicle_id"],
            "telematics_session_id": hub["telematics_session_id"],
            "device_id": obd["device_id"],
            "trip_id": trip["trip_id"],
            "health_id": health["health_id"],
            "diagnostics_id": diag["diagnostics_id"],
            "prediction_id": pred["prediction_id"],
            "fleet_dashboard_id": fleet_dash["dashboard_id"],
            "executive_dashboard_id": exec_dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "core": self.core.status(),
            "telematics": self.telematics.status(),
            "remote": self.remote.status(),
            "predictive": self.predictive.status(),
            "fleet": self.fleet.status(),
            "smart": self.smart.status(),
            "dashboard": self.dashboard.status(),
            "knowledge": self.knowledge.status(),
        }


connected_cars = ConnectedCarsSuite()
