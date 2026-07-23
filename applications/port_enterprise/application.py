# PortEnterpriseApplication — Sprint 15.0 foundation.

from __future__ import annotations

from typing import Any

from applications.port_enterprise.ai_port_director.facade import AIPortDirectorSuite
from applications.port_enterprise.cargo_fleet import CargoManagement, FleetRegistry, ShippingCompanies
from applications.port_enterprise.config import DEFAULT_CONFIG, PortEnterpriseConfig
from applications.port_enterprise.container_management.facade import ContainerManagementSuite
from applications.port_enterprise.customs_trade.facade import CustomsTradeSuite
from applications.port_enterprise.freight_marketplace.facade import FreightMarketplaceSuite
from applications.port_enterprise.multimodal_logistics.facade import MultimodalLogisticsSuite
from applications.port_enterprise.navigation.facade import NavigationSuite
from applications.port_enterprise.operations import PortDashboard, PortKnowledge, PortOperations
from applications.port_enterprise.registry import PortRegistry, TerminalManagement
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store
from applications.port_enterprise.warehouse_distribution.facade import WarehouseDistributionSuite


class PortEnterpriseApplication:
    def __init__(
        self,
        *,
        config: PortEnterpriseConfig | None = None,
        store: PortEnterpriseStore | None = None,
        navigation_svc: NavigationSuite | None = None,
        container_mgmt_svc: ContainerManagementSuite | None = None,
        multimodal_svc: MultimodalLogisticsSuite | None = None,
        customs_svc: CustomsTradeSuite | None = None,
        warehouse_svc: WarehouseDistributionSuite | None = None,
        freight_svc: FreightMarketplaceSuite | None = None,
        director_svc: AIPortDirectorSuite | None = None,
    ) -> None:
        self.config = config or DEFAULT_CONFIG
        self.store = store or port_enterprise_store
        self.ports = PortRegistry(self.store)
        self.terminals = TerminalManagement(self.store)
        self.cargo = CargoManagement(self.store)
        self.shipping = ShippingCompanies(self.store)
        self.fleet = FleetRegistry(self.store)
        self.operations = PortOperations(self.store)
        self.dashboard = PortDashboard(self.store)
        self.knowledge = PortKnowledge(self.store)
        self.navigation = navigation_svc or NavigationSuite(self.store)
        self.container_management = container_mgmt_svc or ContainerManagementSuite(self.store)
        self.multimodal_logistics = multimodal_svc or MultimodalLogisticsSuite(self.store)
        self.customs_trade = customs_svc or CustomsTradeSuite(self.store)
        self.warehouse_distribution = warehouse_svc or WarehouseDistributionSuite(self.store)
        self.freight_marketplace = freight_svc or FreightMarketplaceSuite(self.store)
        self.ai_port_director = director_svc or AIPortDirectorSuite(self.store)

    def reset(self) -> None:
        self.store.reset()

    def bootstrap(self) -> dict[str, Any]:
        port = self.ports.register_port(name="Port of Odessa", unlocode="UAODS", country="UA")
        term = self.ports.register_terminal(
            port_id=port["port_id"], name="Container Terminal 1", terminal_type="container"
        )
        self.ports.register_terminal(port_id=port["port_id"], name="Bulk Terminal", terminal_type="bulk")
        self.ports.register_terminal(port_id=port["port_id"], name="Liquid Terminal", terminal_type="liquid")
        self.ports.register_terminal(port_id=port["port_id"], name="Ro-Ro Terminal", terminal_type="roro")
        self.ports.register_terminal(port_id=port["port_id"], name="Passenger Terminal", terminal_type="passenger")
        dock = self.ports.register_dock(terminal_id=term["terminal_id"], name="Dock A")
        berth = self.ports.register_berth(dock_id=dock["dock_id"], name="Berth A1", length_m=350)
        self.ports.register_warehouse(port_id=port["port_id"], name="CFS Warehouse", capacity_teu=2000)
        self.ports.register_yard(port_id=port["port_id"], name="Yard North", capacity_teu=8000)
        self.ports.register_equipment(terminal_id=term["terminal_id"], name="STS Crane 1", equipment_type="sts_crane")
        cap = self.terminals.set_capacity(terminal_id=term["terminal_id"], capacity_teu=12000, utilized_teu=7800)

        line = self.shipping.register_line(name="Black Sea Line", scac="BSL1")
        self.shipping.register_carrier(name="Ocean Carrier Co", mode="ocean")
        operator = self.shipping.register_operator(name="Vessel Ops Ltd")
        self.shipping.register_agency(name="Odessa Port Agency", port_id=port["port_id"])
        self.shipping.register_provider(name="Harbor Pilots", service="pilotage")

        vessel = self.fleet.register_vessel(
            name="MV Horizon",
            imo="9123456",
            flag="LR",
            owner="Horizon Shipping",
            loa_m=280,
            dwt=45000,
            operator_id=operator["operator_id"],
        )

        cargo = self.cargo.register(
            description="Reefer containers lot A",
            category="refrigerated",
            weight_t=420,
            port_id=port["port_id"],
        )
        self.cargo.register(description="IMO Class 3 chemicals", category="hazardous", weight_t=80, port_id=port["port_id"])
        self.cargo.register(description="Project modules", category="oversized", weight_t=210, port_id=port["port_id"])
        self.cargo.track(cargo["cargo_id"], status="in_yard", location="Yard North")

        arrival = self.operations.plan_arrival(
            vessel_id=vessel["vessel_id"], port_id=port["port_id"], eta="2026-08-10T06:00:00Z"
        )
        departure = self.operations.plan_departure(
            vessel_id=vessel["vessel_id"], port_id=port["port_id"], etd="2026-08-12T18:00:00Z"
        )
        self.operations.schedule_dock(
            dock_id=dock["dock_id"],
            vessel_id=vessel["vessel_id"],
            window_start="2026-08-10T08:00:00Z",
            window_end="2026-08-12T16:00:00Z",
        )
        alloc = self.operations.allocate_berth(berth_id=berth["berth_id"], vessel_id=vessel["vessel_id"])
        self.operations.enqueue_loading(cargo_id=cargo["cargo_id"], vessel_id=vessel["vessel_id"], priority=2)
        self.operations.enqueue_unloading(cargo_id=cargo["cargo_id"], vessel_id=vessel["vessel_id"], priority=3)
        turnaround = self.operations.turnaround_analytics(port["port_id"])

        for base, key in (
            ("port", port["port_id"]),
            ("terminal", term["terminal_id"]),
            ("fleet", vessel["vessel_id"]),
            ("cargo", cargo["cargo_id"]),
            ("shipping", line["line_id"]),
        ):
            self.knowledge.publish(base=base, key=key, payload={"bootstrap": True})

        dash = self.dashboard.render(dashboard_type="operations")
        return {
            "bootstrap": True,
            "port_id": port["port_id"],
            "terminal_id": term["terminal_id"],
            "dock_id": dock["dock_id"],
            "berth_id": berth["berth_id"],
            "capacity_id": cap["capacity_id"],
            "vessel_id": vessel["vessel_id"],
            "cargo_id": cargo["cargo_id"],
            "arrival_id": arrival["arrival_id"],
            "departure_id": departure["departure_id"],
            "allocation_id": alloc["allocation_id"],
            "turnaround": turnaround,
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
            "port_enterprise_foundation_ready": True,
            "terminal_platform_ready": True,
            "cargo_registry_ready": True,
            "fleet_registry_ready": True,
            "operations_foundation_ready": True,
            "vts_platform_ready": True,
            "ais_integration_ready": True,
            "radar_intelligence_ready": True,
            "navigation_platform_ready": True,
            "maritime_safety_ready": True,
            "container_platform_ready": True,
            "yard_automation_ready": True,
            "port_equipment_ready": True,
            "digital_twin_ready": True,
            "terminal_automation_ready": True,
            "rail_logistics_ready": True,
            "truck_logistics_ready": True,
            "multimodal_platform_ready": True,
            "shipment_management_ready": True,
            "ai_logistics_ready": True,
            "customs_platform_ready": True,
            "border_control_ready": True,
            "international_trade_ready": True,
            "trade_compliance_ready": True,
            "ai_trade_intelligence_ready": True,
            "warehouse_platform_ready": True,
            "distribution_centers_ready": True,
            "free_economic_zones_ready": True,
            "warehouse_automation_ready": True,
            "ai_warehouse_ready": True,
            "freight_marketplace_ready": True,
            "freight_exchange_ready": True,
            "global_logistics_network_ready": True,
            "ai_logistics_marketplace_ready": True,
            "carrier_platform_ready": True,
            "ai_port_director_ready": True,
            "predictive_logistics_ready": True,
            "autonomous_operations_ready": True,
            "executive_intelligence_ready": True,
            "engines": {
                "port_registry": self.config.port_registry,
                "terminal_management": self.config.terminal_management,
                "cargo_management": self.config.cargo_management,
                "shipping_companies": self.config.shipping_companies,
                "fleet_registry": self.config.fleet_registry,
                "port_operations": self.config.port_operations,
                "navigation": self.config.navigation,
                "container_management": self.config.container_management,
                "multimodal_logistics": self.config.multimodal_logistics,
                "customs_trade": self.config.customs_trade,
                "warehouse_distribution": self.config.warehouse_distribution,
                "freight_marketplace": self.config.freight_marketplace,
                "ai_port_director": self.config.ai_port_director,
                "knowledge": self.config.knowledge,
                "analytics": self.config.analytics,
            },
            "ports": self.ports.status(),
            "terminals": self.terminals.status(),
            "cargo": self.cargo.status(),
            "shipping": self.shipping.status(),
            "fleet": self.fleet.status(),
            "operations": self.operations.status(),
            "knowledge": self.knowledge.status(),
            "dashboard": self.dashboard.status(),
            "navigation": self.navigation.status(),
            "container_management": self.container_management.status(),
            "multimodal_logistics": self.multimodal_logistics.status(),
            "customs_trade": self.customs_trade.status(),
            "warehouse_distribution": self.warehouse_distribution.status(),
            "freight_marketplace": self.freight_marketplace.status(),
            "ai_port_director": self.ai_port_director.status(),
        }


port_enterprise = PortEnterpriseApplication()
