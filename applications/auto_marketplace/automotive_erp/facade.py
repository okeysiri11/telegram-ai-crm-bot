"""Automotive ERP Suite facade — Sprint 13.6."""

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.automotive_erp.fleet import FleetManagement
from applications.auto_marketplace.automotive_erp.parts import PartsManagement
from applications.auto_marketplace.automotive_erp.service_center import ServiceCenter
from applications.auto_marketplace.automotive_erp.services import (
    EnterpriseERP,
    ERPAnalytics,
    ERPIntegrations,
    MaintenanceAI,
)
from applications.auto_marketplace.config import DEFAULT_CONFIG
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class AutomotiveERPSuite:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.service = ServiceCenter(self.store)
        self.fleet = FleetManagement(self.store)
        self.parts = PartsManagement(self.store)
        self.maintenance_ai = MaintenanceAI(self.store)
        self.enterprise = EnterpriseERP(self.store)
        self.analytics = ERPAnalytics(self.store)
        self.integrations = ERPIntegrations(self.store)

    def bootstrap(self) -> dict[str, Any]:
        mech = self.service.register_mechanic(name="Alex Tech", specialty="diagnostics")
        so = self.service.create_service_order(vin="WVWZZZ1JZXW000001", customer="Prime Motors", description="Annual service")
        ro = self.service.create_repair_order(service_order_id=so["service_order_id"], tasks=["oil_change", "inspection"], parts=["OIL-5W30"])
        self.service.schedule(so["service_order_id"], mechanic_id=mech["mechanic_id"], starts_at="2026-07-25T09:00:00Z")
        qc = self.service.quality_control(so["service_order_id"], passed=True, notes="OK")

        fleet = self.fleet.create_fleet(name="Corporate Fleet EU", operator="Acme Mobility")
        vehicle = self.fleet.add_vehicle(fleet_id=fleet["fleet_id"], vin="1HGCM82633A000001", label="Fleet-01")
        driver = self.fleet.register_driver(name="Sam Driver", license_id="DL-100")
        self.fleet.assign_vehicle(fleet_vehicle_id=vehicle["fleet_vehicle_id"], driver_id=driver["driver_id"])
        trip = self.fleet.log_trip(fleet_vehicle_id=vehicle["fleet_vehicle_id"], distance_km=120, fuel_liters=9.5)
        self.fleet.schedule_maintenance(fleet_vehicle_id=vehicle["fleet_vehicle_id"], due_at="2026-08-01T00:00:00Z")

        part = self.parts.add_part(sku="BRAKE-PAD-F", name="Front Brake Pads", warehouse="main", qty=20, unit_cost=45)
        supplier = self.parts.register_supplier(name="AutoParts Co", contact="orders@parts.example")
        po = self.parts.create_purchase_order(supplier_id=supplier["supplier_id"], items=[{"sku": "BRAKE-PAD-F", "qty": 50}])
        self.parts.reserve(part_id=part["part_id"], qty=2, ref=ro["repair_order_id"])
        self.parts.track_serial(part_id=part["part_id"], serial="SN-BP-001")
        self.parts.forecast(warehouse="main")

        pred = self.maintenance_ai.predict(vin="1HGCM82633A000001", mileage=85000, health_score=72, recent_failures=1)
        invoice = self.enterprise.create_invoice(customer="Prime Motors", amount=350, ref=so["service_order_id"])
        contract = self.enterprise.create_contract(party="Acme Mobility", contract_type="fleet_service")
        self.enterprise.procurement_request(title="Brake pads restock", budget=2500)
        self.enterprise.portal_access(portal="customer", principal="ceo@acme.example")
        self.enterprise.portal_access(portal="employee", principal="alex.tech")

        self.integrations.connect(target="vin_intelligence", endpoint="/api/vin-intelligence/v1")
        self.integrations.connect(target="inspection_ai", endpoint="/api/inspection-ai/v1")
        self.integrations.connect(target="dealer_crm", endpoint="/api/dealer-crm/v1")
        self.integrations.connect(target="ai_os", endpoint="/api/ai-os/v1")
        report = self.analytics.report(report_type="executive")
        dash = self.fleet.dashboard(fleet["fleet_id"])
        return {
            "bootstrap": True,
            "mechanic_id": mech["mechanic_id"],
            "service_order_id": so["service_order_id"],
            "repair_order_id": ro["repair_order_id"],
            "history_id": qc["history_id"],
            "fleet_id": fleet["fleet_id"],
            "fleet_vehicle_id": vehicle["fleet_vehicle_id"],
            "trip_id": trip["trip_id"],
            "part_id": part["part_id"],
            "purchase_order_id": po["purchase_order_id"],
            "prediction_id": pred["prediction_id"],
            "invoice_id": invoice["invoice_id"],
            "contract_id": contract["contract_id"],
            "report_id": report["report_id"],
            "fleet_dashboard": dash,
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "service": self.service.status(),
            "fleet": self.fleet.status(),
            "parts": self.parts.status(),
            "maintenance_ai": self.maintenance_ai.status(),
            "enterprise": self.enterprise.status(),
            "analytics": self.analytics.status(),
            "integrations": self.integrations.status(),
        }


automotive_erp = AutomotiveERPSuite()
