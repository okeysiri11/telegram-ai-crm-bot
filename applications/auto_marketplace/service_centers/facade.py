# Service domain facade — Sprint 10.5.

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.appointments.engine import ServiceAppointmentEngine, service_appointment_engine
from applications.auto_marketplace.diagnostics.engine import DiagnosticsEngine, diagnostics_engine
from applications.auto_marketplace.inventory.parts_engine import PartsInventoryEngine, parts_inventory_engine
from applications.auto_marketplace.maintenance.engine import VehicleMaintenanceEngine, vehicle_maintenance_engine
from applications.auto_marketplace.parts.engine import PartsMarketplaceEngine, parts_marketplace_engine
from applications.auto_marketplace.repair_orders.engine import RepairOrderEngine, repair_order_engine
from applications.auto_marketplace.service_centers.engine import ServiceCenterEngine, service_center_engine
from applications.auto_marketplace.service_history.engine import ServiceHistoryEngine, service_history_engine
from applications.auto_marketplace.suppliers.engine import SupplierEngine, supplier_engine
from applications.auto_marketplace.warranty.engine import WarrantyEngine, warranty_engine


class ServiceDomainEngine:
    """Sprint 10.5 — service centers, repairs, parts, maintenance, warranty."""

    def __init__(
        self,
        centers: ServiceCenterEngine | None = None,
        repair_orders: RepairOrderEngine | None = None,
        maintenance: VehicleMaintenanceEngine | None = None,
        appointments: ServiceAppointmentEngine | None = None,
        parts: PartsMarketplaceEngine | None = None,
        inventory: PartsInventoryEngine | None = None,
        suppliers: SupplierEngine | None = None,
        warranty: WarrantyEngine | None = None,
        diagnostics: DiagnosticsEngine | None = None,
        history: ServiceHistoryEngine | None = None,
    ) -> None:
        self.centers = centers or service_center_engine
        self.repair_orders = repair_orders or repair_order_engine
        self.maintenance = maintenance or vehicle_maintenance_engine
        self.appointments = appointments or service_appointment_engine
        self.parts = parts or parts_marketplace_engine
        self.inventory = inventory or parts_inventory_engine
        self.suppliers = suppliers or supplier_engine
        self.warranty = warranty or warranty_engine
        self.diagnostics = diagnostics or diagnostics_engine
        self.history = history or service_history_engine

    def metrics(self) -> dict[str, Any]:
        return {
            "centers": self.centers.metrics(),
            "repair_orders": self.repair_orders.metrics(),
            "maintenance": self.maintenance.metrics(),
            "appointments": self.appointments.metrics(),
            "parts": self.parts.metrics(),
            "inventory": self.inventory.metrics(),
            "suppliers": self.suppliers.metrics(),
            "warranty": self.warranty.metrics(),
            "diagnostics": self.diagnostics.metrics(),
            "history": self.history.metrics(),
        }


service_domain_engine = ServiceDomainEngine()
