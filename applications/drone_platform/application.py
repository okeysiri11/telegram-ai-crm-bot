# DronePlatformApplication — foundation facade (Sprint 11.1).

from __future__ import annotations

from typing import Any

from applications.drone_platform.ai.assistant import EngineeringAIAssistant, engineering_ai
from applications.drone_platform.analytics.service import AnalyticsService, analytics_service
from applications.drone_platform.config import DEFAULT_CONFIG, DronePlatformConfig
from applications.drone_platform.documentation.service import DocumentationService, documentation_service
from applications.drone_platform.engineering.service import EngineeringService, engineering_service
from applications.drone_platform.firmware.service import FirmwareService, firmware_service
from applications.drone_platform.integrations.ecosystem_bridge import EcosystemBridge, ecosystem_bridge
from applications.drone_platform.integrations.platform_bridge import PlatformBridge, platform_bridge
from applications.drone_platform.inventory.service import InventoryService, inventory_service
from applications.drone_platform.manufacturing.service import ManufacturingService, manufacturing_service
from applications.drone_platform.missions.service import MissionService, mission_service
from applications.drone_platform.projects.service import ProjectService, project_service
from applications.drone_platform.registry.service import RegistryService, registry_service
from applications.drone_platform.shared.store import DroneStore, drone_store
from applications.drone_platform.simulation.service import SimulationService, simulation_service
from applications.drone_platform.telemetry.service import TelemetryService, telemetry_service
from applications.drone_platform.warehouse.service import WarehouseService, warehouse_service


class DronePlatformApplication:
    """UAV engineering ERP + AI platform foundation."""

    def __init__(
        self,
        *,
        config: DronePlatformConfig | None = None,
        store: DroneStore | None = None,
        registry: RegistryService | None = None,
        projects: ProjectService | None = None,
        engineering: EngineeringService | None = None,
        firmware: FirmwareService | None = None,
        missions: MissionService | None = None,
        telemetry: TelemetryService | None = None,
        inventory: InventoryService | None = None,
        warehouse: WarehouseService | None = None,
        manufacturing: ManufacturingService | None = None,
        simulation: SimulationService | None = None,
        documentation: DocumentationService | None = None,
        ai: EngineeringAIAssistant | None = None,
        analytics: AnalyticsService | None = None,
        platform: PlatformBridge | None = None,
        ecosystem: EcosystemBridge | None = None,
    ) -> None:
        self.config = config or DEFAULT_CONFIG
        self.store = store or drone_store
        self.registry = registry or registry_service
        self.projects = projects or project_service
        self.engineering = engineering or engineering_service
        self.firmware = firmware or firmware_service
        self.missions = missions or mission_service
        self.telemetry = telemetry or telemetry_service
        self.inventory = inventory or inventory_service
        self.warehouse = warehouse or warehouse_service
        self.manufacturing = manufacturing or manufacturing_service
        self.simulation = simulation or simulation_service
        self.documentation = documentation or documentation_service
        self.ai = ai or engineering_ai
        self.analytics = analytics or analytics_service
        self.platform = platform or platform_bridge
        self.ecosystem = ecosystem or ecosystem_bridge

    def reset(self) -> None:
        self.store.reset()

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "application": self.config.application,
            "application_name": self.config.application_name,
            "application_version": self.config.application_version,
            "release_status": self.config.release_status,
            "api_prefix": self.config.api_prefix,
            "foundation_ready": True,
            "engineering_ready": True,
            "firmware_workspace_ready": True,
            "mission_planning_ready": True,
            "inventory_ready": True,
            "ai_engineering_assistant_ready": True,
            "engines": {
                "registry": self.config.registry_engine,
                "engineering": self.config.engineering_engine,
                "firmware": self.config.firmware_engine,
                "mission": self.config.mission_engine,
                "inventory": self.config.inventory_engine,
                "ai": self.config.ai_engine,
            },
            "bridges": {
                "platform": self.platform.health(),
                "ecosystem": self.ecosystem.health(),
            },
            "analytics": self.analytics.overview(),
        }


drone_platform = DronePlatformApplication()
