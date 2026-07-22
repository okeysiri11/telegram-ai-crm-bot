"""Controlled Environment Suite facade — Sprint 14.4."""

from __future__ import annotations

from typing import Any

from applications.agro_enterprise.config import DEFAULT_CONFIG
from applications.agro_enterprise.controlled_environment.greenhouse import (
    ControlledEnvironmentAI,
    GreenhouseManagement,
)
from applications.agro_enterprise.controlled_environment.livestock import (
    Aquaculture,
    Biosecurity,
    FeedNutrition,
    LivestockManagement,
    PoultryManagement,
)
from applications.agro_enterprise.controlled_environment.services import CEADashboard, CEAKnowledge
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store


class ControlledEnvironmentSuite:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.greenhouse = GreenhouseManagement(self.store)
        self.climate_ai = ControlledEnvironmentAI(self.store)
        self.livestock = LivestockManagement(self.store)
        self.poultry = PoultryManagement(self.store)
        self.aquaculture = Aquaculture(self.store)
        self.feed = FeedNutrition(self.store)
        self.biosecurity = Biosecurity(self.store)
        self.dashboard = CEADashboard(self.store)
        self.knowledge = CEAKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        gh = self.greenhouse.register_greenhouse(name="Glasshouse A", area_m2=2500, location="NL")
        zone = self.greenhouse.create_zone(greenhouse_id=gh["greenhouse_id"], name="Tomato Bay 1")
        self.greenhouse.set_climate(zone["zone_id"], temp_c=23.5, humidity_pct=68, co2_ppm=900)
        self.greenhouse.control(zone["zone_id"], control="lighting", enabled=True, setpoint=180)
        self.greenhouse.control(zone["zone_id"], control="ventilation", enabled=True)
        self.greenhouse.control(zone["zone_id"], control="heating", enabled=False)
        self.greenhouse.control(zone["zone_id"], control="cooling", enabled=True)
        self.greenhouse.schedule_crop(zone_id=zone["zone_id"], crop="tomato", starts_at="2026-03-01")
        self.greenhouse.record_yield(zone_id=zone["zone_id"], kg=420)
        opt = self.climate_ai.optimize(zone_id=zone["zone_id"], temp_c=23.5, humidity_pct=68)

        breed = self.livestock.register_breed(name="Holstein", species="cattle")
        animal = self.livestock.register_animal(tag="NL-1001", breed_id=breed["breed_id"])
        self.livestock.health(animal["animal_id"], health_score=88, note="routine")
        self.livestock.vaccinate(animal["animal_id"], vaccine="BVD")
        self.livestock.feed(animal["animal_id"], ration_kg=18)
        self.livestock.weigh(animal["animal_id"], weight_kg=620)
        self.livestock.milk(animal["animal_id"], liters=28)
        self.livestock.reproduction(animal["animal_id"], status="open")

        flock = self.poultry.register_flock(name="Layer House 2", birds=5000)
        self.poultry.record_eggs(flock["flock_id"], count=4200)
        self.poultry.mortality(flock["flock_id"], count=3, reason="natural")

        aqua = self.aquaculture.register_farm(name="Recirc Pond 1", species="tilapia")
        self.aquaculture.water_quality(aqua["farm_id"], oxygen_mg_l=6.2, temp_c=27, ph=7.2)
        self.aquaculture.feed(aqua["farm_id"], kg=40)
        growth = self.aquaculture.growth_prediction(aqua["farm_id"], biomass_kg=1200, days=40)

        self.feed.add_inventory(sku="LAYER-MASH", kg=2000, cost_per_kg=0.42)
        self.feed.formulate(name="Dairy TMR", ingredients={"silage": 0.5, "grain": 0.3, "protein": 0.2})

        self.biosecurity.access(site="Glasshouse A", principal="tech1", granted=True)
        self.biosecurity.quarantine(subject=animal["animal_id"], reason="new_arrival")
        self.biosecurity.incident(title="Fence breach", severity="low")
        self.biosecurity.sanitation(area="Poultry Hall")
        self.biosecurity.compliance(framework="GAP", status="compliant")

        for rtype, key in (
            ("greenhouse", gh["greenhouse_id"]),
            ("livestock", animal["animal_id"]),
            ("poultry", flock["flock_id"]),
            ("aquaculture", aqua["farm_id"]),
            ("biosecurity", "GAP"),
        ):
            self.knowledge.publish(registry_type=rtype, key=key, payload={"bootstrap": True})

        dash = self.dashboard.render(dashboard_type="production")
        return {
            "bootstrap": True,
            "greenhouse_id": gh["greenhouse_id"],
            "zone_id": zone["zone_id"],
            "optimization_id": opt["optimization_id"],
            "animal_id": animal["animal_id"],
            "flock_id": flock["flock_id"],
            "fish_farm_id": aqua["farm_id"],
            "growth_prediction_id": growth["prediction_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "greenhouse": self.greenhouse.status(),
            "climate_ai": self.climate_ai.status(),
            "livestock": self.livestock.status(),
            "poultry": self.poultry.status(),
            "aquaculture": self.aquaculture.status(),
            "feed": self.feed.status(),
            "biosecurity": self.biosecurity.status(),
            "dashboard": self.dashboard.status(),
            "knowledge": self.knowledge.status(),
        }


controlled_environment = ControlledEnvironmentSuite()
