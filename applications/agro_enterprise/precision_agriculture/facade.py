"""Precision Agriculture Suite facade — Sprint 14.1."""

from __future__ import annotations

from typing import Any

from applications.agro_enterprise.config import DEFAULT_CONFIG
from applications.agro_enterprise.precision_agriculture.fields_gis import FieldManagement, GISPlatform
from applications.agro_enterprise.precision_agriculture.sensing import (
    DroneIntegration,
    IoTSmartFarming,
    SatelliteIntelligence,
)
from applications.agro_enterprise.precision_agriculture.services import (
    AICropMonitoring,
    PrecisionDashboard,
    PrecisionKnowledge,
)
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store


class PrecisionAgricultureSuite:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.fields = FieldManagement(self.store)
        self.gis = GISPlatform(self.store)
        self.drone = DroneIntegration(self.store)
        self.satellite = SatelliteIntelligence(self.store)
        self.iot = IoTSmartFarming(self.store)
        self.ai = AICropMonitoring(self.store)
        self.dashboard = PrecisionDashboard(self.store)
        self.knowledge = PrecisionKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        field = self.fields.register_field(
            name="North Precision Field",
            farm_id="farm_demo",
            hectares=48.5,
            soil_type="chernozem",
            owner="Green Fields",
        )
        self.fields.set_boundary(
            field["field_id"],
            coordinates=[
                {"lat": 50.45, "lon": 30.52},
                {"lat": 50.46, "lon": 30.52},
                {"lat": 50.46, "lon": 30.54},
                {"lat": 50.45, "lon": 30.54},
            ],
        )
        self.fields.assign_crop(field["field_id"], crop_id="crop_wheat")
        self.fields.record_history(field["field_id"], event="scouting", details={"note": "baseline"})

        gmap = self.gis.create_map(name="Field GIS", field_id=field["field_id"], basemap="satellite")
        self.gis.add_layer(gmap["map_id"], layer="ndvi")
        self.gis.add_layer(gmap["map_id"], layer="moisture")
        self.gis.add_layer(gmap["map_id"], layer="elevation")

        mission = self.drone.plan_mission(field_id=field["field_id"], mission_type="crop_monitoring", altitude_m=90)
        flight = self.drone.complete_survey(mission["mission_id"], plant_count=182000, thermal=True)

        imagery = self.satellite.ingest_imagery(field_id=field["field_id"], source="sentinel-2")
        sat = self.satellite.analyze(imagery["imagery_id"])

        weather = self.iot.register_sensor(field_id=field["field_id"], kind="weather", name="WS-1")
        moisture = self.iot.register_sensor(field_id=field["field_id"], kind="soil_moisture", name="SM-1")
        self.iot.register_sensor(field_id=field["field_id"], kind="irrigation", name="IRR-1")
        self.iot.reading(weather["sensor_id"], value=22.5, unit="C")
        self.iot.reading(moisture["sensor_id"], value=31.0, unit="%")
        self.iot.irrigate(field_id=field["field_id"], duration_min=25)

        ai = self.ai.analyze(field_id=field["field_id"], ndvi=0.58, stress_index=0.25, growth_day=72)
        for rtype, key in (
            ("field", field["field_id"]),
            ("crop_monitoring", ai["analysis_id"]),
            ("drone_mission", mission["mission_id"]),
            ("satellite", imagery["imagery_id"]),
            ("sensor", moisture["sensor_id"]),
        ):
            self.knowledge.publish(registry_type=rtype, key=key, payload={"bootstrap": True})

        dash = self.dashboard.render(dashboard_type="crop_health")
        return {
            "bootstrap": True,
            "field_id": field["field_id"],
            "map_id": gmap["map_id"],
            "mission_id": mission["mission_id"],
            "flight_id": flight["flight_id"],
            "imagery_id": imagery["imagery_id"],
            "satellite_analysis_id": sat["analysis_id"],
            "ai_analysis_id": ai["analysis_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "fields": self.fields.status(),
            "gis": self.gis.status(),
            "drone": self.drone.status(),
            "satellite": self.satellite.status(),
            "iot": self.iot.status(),
            "ai": self.ai.status(),
            "dashboard": self.dashboard.status(),
            "knowledge": self.knowledge.status(),
        }


precision_agriculture = PrecisionAgricultureSuite()
