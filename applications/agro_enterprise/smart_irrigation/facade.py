"""Smart Irrigation Suite facade — Sprint 14.2."""

from __future__ import annotations

from typing import Any

from applications.agro_enterprise.config import DEFAULT_CONFIG
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store
from applications.agro_enterprise.smart_irrigation.control_iot import IrrigationIoT, SmartIrrigationControl
from applications.agro_enterprise.smart_irrigation.services import (
    AIIrrigation,
    EnvironmentalIntelligence,
    IrrigationDashboard,
    IrrigationKnowledge,
)
from applications.agro_enterprise.smart_irrigation.soil_water import SoilIntelligence, WaterManagement


class SmartIrrigationSuite:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.soil = SoilIntelligence(self.store)
        self.water = WaterManagement(self.store)
        self.irrigation = SmartIrrigationControl(self.store)
        self.iot = IrrigationIoT(self.store)
        self.ai = AIIrrigation(self.store)
        self.environment = EnvironmentalIntelligence(self.store)
        self.dashboard = IrrigationDashboard(self.store)
        self.knowledge = IrrigationKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        soil = self.soil.register_soil(
            field_id="field_north",
            organic_matter_pct=3.2,
            ph=6.8,
            salinity_ds_m=0.6,
            compaction_mpa=1.1,
        )
        self.soil.nutrient_analysis(soil["soil_id"], n=52, p=28, k=210)

        source = self.water.register_source(name="Main Reservoir", source_type="reservoir", capacity_m3=5000)
        self.water.register_source(name="Canal East", source_type="canal", capacity_m3=1200)
        self.water.register_source(name="Well A", source_type="groundwater", capacity_m3=800)
        self.water.update_level(source["source_id"], level_m3=4100)
        self.water.log_consumption(source_id=source["source_id"], volume_m3=45, zone_id="pending")
        balance = self.water.water_balance(source["source_id"])
        self.water.quality_check(source["source_id"], turbidity=1.5, ph=7.1)

        zone = self.irrigation.create_zone(name="Zone Alpha", field_id="field_north", hectares=12)
        self.water.log_consumption(source_id=source["source_id"], volume_m3=12, zone_id=zone["zone_id"])
        schedule = self.irrigation.schedule(zone_id=zone["zone_id"], starts_at="2026-07-23T06:00:00Z", duration_min=40)
        self.irrigation.set_pump(source_id=source["source_id"], running=True, flow_m3h=18)
        self.irrigation.remote_control(zone_id=zone["zone_id"], command="start")
        flow = self.irrigation.monitor_flow(zone_id=zone["zone_id"], flow_lpm=120, pressure_bar=2.8)

        gw = self.iot.register_gateway(name="Field GW-1", field_id="field_north")
        moisture = self.iot.register_sensor(kind="soil_moisture", gateway_id=gw["gateway_id"], name="SM-A")
        self.iot.register_sensor(kind="rain", gateway_id=gw["gateway_id"], name="RAIN-1")
        self.iot.register_sensor(kind="solar_radiation", gateway_id=gw["gateway_id"], name="SOLAR-1")
        self.iot.reading(moisture["sensor_id"], value=28.5, unit="%")

        pred = self.ai.predict(
            zone_id=zone["zone_id"],
            soil_moisture_pct=28.5,
            et0_mm=5.2,
            forecast_rain_mm=1.0,
            water_cost_per_m3=0.35,
        )
        self.environment.ingest_weather(region="EU-East", temp_c=29, humidity_pct=42, rain_mm=0.2)
        risk = self.environment.assess_risks(region="EU-East", soil_moisture_pct=28.5, temp_c=29)

        for rtype, key in (
            ("soil", soil["soil_id"]),
            ("water", source["source_id"]),
            ("irrigation", zone["zone_id"]),
            ("sensor", moisture["sensor_id"]),
            ("environmental", risk["risk_id"]),
        ):
            self.knowledge.publish(registry_type=rtype, key=key, payload={"bootstrap": True})

        dash = self.dashboard.render(dashboard_type="ai_recommendation")
        return {
            "bootstrap": True,
            "soil_id": soil["soil_id"],
            "source_id": source["source_id"],
            "balance_id": balance["balance_id"],
            "zone_id": zone["zone_id"],
            "schedule_id": schedule["schedule_id"],
            "flow_id": flow["monitor_id"],
            "prediction_id": pred["prediction_id"],
            "risk_id": risk["risk_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "soil": self.soil.status(),
            "water": self.water.status(),
            "irrigation": self.irrigation.status(),
            "iot": self.iot.status(),
            "ai": self.ai.status(),
            "environment": self.environment.status(),
            "dashboard": self.dashboard.status(),
            "knowledge": self.knowledge.status(),
        }


smart_irrigation = SmartIrrigationSuite()
