# AgroEnterpriseApplication — Sprint 14.0 foundation.

from __future__ import annotations

from typing import Any

from applications.agro_enterprise.config import DEFAULT_CONFIG, AgroEnterpriseConfig
from applications.agro_enterprise.crops_crm import AgroCRM, CropManagement
from applications.agro_enterprise.marketplace import AgroMarketplace, FarmRegistry
from applications.agro_enterprise.controlled_environment.facade import ControlledEnvironmentSuite
from applications.agro_enterprise.crop_ai.facade import CropAISuite
from applications.agro_enterprise.precision_agriculture.facade import PrecisionAgricultureSuite
from applications.agro_enterprise.services import AgroDashboard, AgroKnowledge
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store
from applications.agro_enterprise.smart_irrigation.facade import SmartIrrigationSuite


class AgroEnterpriseApplication:
    def __init__(
        self,
        *,
        config: AgroEnterpriseConfig | None = None,
        store: AgroEnterpriseStore | None = None,
        precision: PrecisionAgricultureSuite | None = None,
        irrigation: SmartIrrigationSuite | None = None,
        crop_ai_svc: CropAISuite | None = None,
        controlled_environment_svc: ControlledEnvironmentSuite | None = None,
    ) -> None:
        self.config = config or DEFAULT_CONFIG
        self.store = store or agro_enterprise_store
        self.marketplace = AgroMarketplace(self.store)
        self.farms = FarmRegistry(self.store)
        self.crops = CropManagement(self.store)
        self.crm = AgroCRM(self.store)
        self.knowledge = AgroKnowledge(self.store)
        self.dashboard = AgroDashboard(self.store)
        self.precision = precision or PrecisionAgricultureSuite(self.store)
        self.irrigation = irrigation or SmartIrrigationSuite(self.store)
        self.crop_ai = crop_ai_svc or CropAISuite(self.store)
        self.controlled_environment = controlled_environment_svc or ControlledEnvironmentSuite(self.store)

    def reset(self) -> None:
        self.store.reset()

    def bootstrap(self) -> dict[str, Any]:
        supplier = self.marketplace.register_supplier(name="SeedCo Supply", region="EU-East")
        buyer = self.marketplace.register_buyer(name="Grain Traders Ltd", region="EU-Central")
        listing = self.marketplace.create_listing(
            category="crops",
            side="sell",
            title="Winter Wheat Grade A",
            quantity=120,
            unit="t",
            price=240,
            party_id=supplier["supplier_id"],
        )
        self.marketplace.create_listing(
            category="seeds", side="buy", title="Hybrid maize seed", quantity=5, unit="t", price=1800, party_id=buyer["buyer_id"]
        )
        self.marketplace.create_listing(
            category="fertilizers", side="sell", title="NPK 16-16-16", quantity=40, unit="t", price=520, party_id=supplier["supplier_id"]
        )
        self.marketplace.create_listing(
            category="equipment", side="sell", title="Combine harvester lease", quantity=1, unit="unit", price=85000, party_id=supplier["supplier_id"]
        )
        self.marketplace.create_listing(
            category="services", side="sell", title="Soil analysis service", quantity=1, unit="job", price=450, party_id=supplier["supplier_id"]
        )
        order = self.marketplace.place_order(listing_id=listing["listing_id"], counterparty_id=buyer["buyer_id"], quantity=50)

        company = self.farms.create_company(name="Green Fields Holding")
        farm = self.farms.create_farm(name="Green Fields Farm", owner=company["name"], region="Ukraine", hectares=850)
        land = self.farms.register_farmland(farm_id=farm["farm_id"], label="North Field", hectares=220)
        self.farms.register_storage(farm_id=farm["farm_id"], name="Silo-1", capacity_t=2000)
        self.farms.register_equipment(farm_id=farm["farm_id"], name="John Deere 6R", equipment_type="tractor")
        self.farms.register_livestock(farm_id=farm["farm_id"], species="cattle", headcount=40)
        self.farms.add_certification(farm_id=farm["farm_id"], standard="Organic-EU")

        crop = self.crops.add_crop(name="Winter Wheat", variety="Bohdana", season="winter")
        self.crops.plan_season(farm_id=farm["farm_id"], year=2026, crops=[crop["crop_id"]])
        self.crops.crop_rotation(farm_id=farm["farm_id"], sequence=["wheat", "sunflower", "maize"])
        self.crops.assign_field(farm_id=farm["farm_id"], land_id=land["land_id"], crop_id=crop["crop_id"])
        yield_plan = self.crops.yield_plan(crop_id=crop["crop_id"], hectares=220, expected_t_per_ha=5.2)
        self.crops.harvest_plan(crop_id=crop["crop_id"], window_start="2026-07-10", window_end="2026-07-25")
        self.crops.calendar_entry(farm_id=farm["farm_id"], title="Seeding window", date="2026-09-15")

        farmer = self.crm.create_contact(name="Ivan Farmer", crm_type="farmer", company=farm["name"])
        self.crm.create_contact(name="SeedCo Rep", crm_type="supplier", company=supplier["name"])
        self.crm.create_contact(name="Grain Desk", crm_type="buyer", company=buyer["name"])
        contract = self.crm.create_contract(party_id=farmer["contact_id"], title="Wheat offtake 2026", value=120000)
        self.crm.create_lead(name="Coop Cooperative", source="marketplace", score=0.8)
        self.crm.create_task(title="Confirm harvest logistics", assignee="ops", due_at="2026-07-01")
        self.crm.calendar_event(title="Supplier review", starts_at="2026-06-01T10:00:00Z")

        self.knowledge.publish(base="crop", title="Winter wheat agronomy", body="Seeding rates and frost risk", tags=["wheat"])
        self.knowledge.publish(base="soil", title="Chernozem profile", body="High organic matter soils", tags=["soil"])
        self.knowledge.publish(base="equipment", title="Combine setup", body="Header and loss settings", tags=["harvest"])
        self.knowledge.publish(base="regulations", title="EU organic labeling", body="Traceability requirements", tags=["compliance"])

        dash = self.dashboard.render(dashboard_type="executive")
        return {
            "bootstrap": True,
            "supplier_id": supplier["supplier_id"],
            "buyer_id": buyer["buyer_id"],
            "listing_id": listing["listing_id"],
            "order_id": order["order_id"],
            "farm_id": farm["farm_id"],
            "crop_id": crop["crop_id"],
            "yield_plan_id": yield_plan["yield_plan_id"],
            "contract_id": contract["contract_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": self.config.application_version,
        }

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "application": self.config.application,
            "application_name": self.config.application_name,
            "application_version": self.config.application_version,
            "release_status": self.config.release_status,
            "enterprise_foundation": self.config.enterprise_foundation,
            "platform_dependency": self.config.platform_dependency,
            "ecosystem_dependency": self.config.ecosystem_dependency,
            "api_prefix": self.config.api_prefix,
            "agro_marketplace_ready": True,
            "farm_registry_ready": True,
            "crop_management_ready": True,
            "agro_crm_ready": True,
            "precision_agriculture_ready": True,
            "gis_platform_ready": True,
            "drone_integration_ready": True,
            "satellite_intelligence_ready": True,
            "smart_fields_ready": True,
            "smart_irrigation_ready": True,
            "soil_intelligence_ready": True,
            "water_management_ready": True,
            "environmental_ai_ready": True,
            "crop_ai_ready": True,
            "disease_detection_ready": True,
            "pest_intelligence_ready": True,
            "yield_intelligence_ready": True,
            "autonomous_farm_ready": True,
            "smart_greenhouse_ready": True,
            "livestock_platform_ready": True,
            "poultry_platform_ready": True,
            "aquaculture_platform_ready": True,
            "controlled_environment_agriculture_ready": True,
            "engines": {
                "agro_marketplace": self.config.agro_marketplace,
                "farm_registry": self.config.farm_registry,
                "crop_management": self.config.crop_management,
                "agro_crm": self.config.agro_crm,
                "knowledge": self.config.knowledge,
                "analytics": self.config.analytics,
                "precision_agriculture": self.config.precision_agriculture,
                "smart_irrigation": self.config.smart_irrigation,
                "crop_ai": self.config.crop_ai,
                "controlled_environment": self.config.controlled_environment,
            },
            "marketplace": self.marketplace.status(),
            "farms": self.farms.status(),
            "crops": self.crops.status(),
            "crm": self.crm.status(),
            "knowledge": self.knowledge.status(),
            "dashboard": self.dashboard.status(),
            "precision": self.precision.status(),
            "irrigation": self.irrigation.status(),
            "crop_ai": self.crop_ai.status(),
            "controlled_environment": self.controlled_environment.status(),
        }


agro_enterprise = AgroEnterpriseApplication()
