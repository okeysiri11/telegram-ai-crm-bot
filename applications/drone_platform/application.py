# DronePlatformApplication — facade (Sprint 11.1–11.4).

from __future__ import annotations

from typing import Any

from applications.drone_platform.ai.vision_ai import VisionFlightAIAssistant, vision_flight_ai
from applications.drone_platform.analytics.service import AnalyticsService, analytics_service
from applications.drone_platform.autonomy import AutonomyEngine, autonomy_engine
from applications.drone_platform.config import DEFAULT_CONFIG, DronePlatformConfig
from applications.drone_platform.diagnostics import FlightDiagnosticsService, flight_diagnostics
from applications.drone_platform.documentation.service import DocumentationService, documentation_service
from applications.drone_platform.engineering.service import EngineeringService, engineering_service
from applications.drone_platform.firmware.ardupilot import ArduPilotService, ardupilot_service
from applications.drone_platform.firmware.manager import FirmwareManager, firmware_manager
from applications.drone_platform.firmware.mission_planner import MissionPlannerBridge, mission_planner_bridge
from applications.drone_platform.firmware.service import FirmwareService, firmware_service
from applications.drone_platform.flight_logs import FlightLogService, flight_log_service
from applications.drone_platform.gcs import GCSBridgeService, gcs_bridge_service
from applications.drone_platform.integrations.ecosystem_bridge import EcosystemBridge, ecosystem_bridge
from applications.drone_platform.integrations.platform_bridge import PlatformBridge, platform_bridge
from applications.drone_platform.inventory.service import InventoryService, inventory_service
from applications.drone_platform.manufacturing.service import ManufacturingService, manufacturing_service
from applications.drone_platform.mapping import MappingService, mapping_service
from applications.drone_platform.mavlink import MAVLinkManager, mavlink_manager
from applications.drone_platform.mission_intelligence import MissionIntelligenceManager, mission_intelligence
from applications.drone_platform.missions.service import MissionService, mission_service
from applications.drone_platform.navigation import NavigationEngine, navigation_engine
from applications.drone_platform.projects.service import ProjectService, project_service
from applications.drone_platform.registry.service import RegistryService, registry_service
from applications.drone_platform.shared.store import DroneStore, drone_store
from applications.drone_platform.simulation.service import SimulationService, simulation_service
from applications.drone_platform.telemetry.ai_manager import TelemetryAIManager, telemetry_ai_manager
from applications.drone_platform.telemetry.service import TelemetryService, telemetry_service
from applications.drone_platform.vision import DetectionSuite, VisionManager, detection_suite, vision_manager
from applications.drone_platform.visualization import VisualizationService, visualization_service
from applications.drone_platform.warehouse.service import WarehouseService, warehouse_service


class DronePlatformApplication:
    """UAV engineering + firmware + MAVLink + vision/navigation/autonomy platform."""

    def __init__(
        self,
        *,
        config: DronePlatformConfig | None = None,
        store: DroneStore | None = None,
        registry: RegistryService | None = None,
        projects: ProjectService | None = None,
        engineering: EngineeringService | None = None,
        firmware: FirmwareService | None = None,
        firmware_intel: FirmwareManager | None = None,
        ardupilot: ArduPilotService | None = None,
        mission_planner: MissionPlannerBridge | None = None,
        missions: MissionService | None = None,
        telemetry: TelemetryService | None = None,
        telemetry_ai: TelemetryAIManager | None = None,
        mavlink: MAVLinkManager | None = None,
        flight_logs: FlightLogService | None = None,
        diagnostics: FlightDiagnosticsService | None = None,
        mission_intel: MissionIntelligenceManager | None = None,
        gcs: GCSBridgeService | None = None,
        visualization: VisualizationService | None = None,
        vision: VisionManager | None = None,
        detection: DetectionSuite | None = None,
        navigation: NavigationEngine | None = None,
        mapping: MappingService | None = None,
        autonomy: AutonomyEngine | None = None,
        inventory: InventoryService | None = None,
        warehouse: WarehouseService | None = None,
        manufacturing: ManufacturingService | None = None,
        simulation: SimulationService | None = None,
        documentation: DocumentationService | None = None,
        ai: VisionFlightAIAssistant | None = None,
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
        self.firmware_intel = firmware_intel or firmware_manager
        self.ardupilot = ardupilot or ardupilot_service
        self.mission_planner = mission_planner or mission_planner_bridge
        self.missions = missions or mission_service
        self.telemetry = telemetry or telemetry_service
        self.telemetry_ai = telemetry_ai or telemetry_ai_manager
        self.mavlink = mavlink or mavlink_manager
        self.flight_logs = flight_logs or flight_log_service
        self.diagnostics = diagnostics or flight_diagnostics
        self.mission_intel = mission_intel or mission_intelligence
        self.gcs = gcs or gcs_bridge_service
        self.visualization = visualization or visualization_service
        self.vision = vision or vision_manager
        self.detection = detection or detection_suite
        self.navigation = navigation or navigation_engine
        self.mapping = mapping or mapping_service
        self.autonomy = autonomy or autonomy_engine
        self.inventory = inventory or inventory_service
        self.warehouse = warehouse or warehouse_service
        self.manufacturing = manufacturing or manufacturing_service
        self.simulation = simulation or simulation_service
        self.documentation = documentation or documentation_service
        self.ai = ai or vision_flight_ai
        self.analytics = analytics or analytics_service
        self.platform = platform or platform_bridge
        self.ecosystem = ecosystem or ecosystem_bridge

    def reset(self) -> None:
        self.store.reset()
        self.ardupilot._seed_defaults()

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
            "firmware_intelligence_ready": True,
            "ardupilot_ready": True,
            "mission_planner_ready": True,
            "mavlink_intelligence_ready": True,
            "telemetry_ai_ready": True,
            "flight_log_analysis_ready": True,
            "mission_intelligence_ready": True,
            "gcs_integration_ready": True,
            "drone_diagnostics_ready": True,
            "computer_vision_ready": True,
            "navigation_ai_ready": True,
            "autonomous_flight_ready": True,
            "slam_ready": True,
            "simulation_ready": True,
            "drone_ai_vision_platform_ready": True,
            "mission_planning_ready": True,
            "inventory_ready": True,
            "ai_engineering_assistant_ready": True,
            "firmware_ai_assistant_ready": True,
            "telemetry_flight_ai_ready": True,
            "vision_flight_ai_ready": True,
            "engines": {
                "registry": self.config.registry_engine,
                "engineering": self.config.engineering_engine,
                "firmware": self.config.firmware_engine,
                "firmware_intelligence": self.config.firmware_intelligence,
                "ardupilot": self.config.ardupilot_engine,
                "mission_planner": self.config.mission_planner_bridge,
                "mavlink": self.config.mavlink_engine,
                "telemetry_ai": self.config.telemetry_ai_engine,
                "flight_logs": self.config.flight_log_engine,
                "mission_intelligence": self.config.mission_intelligence_engine,
                "diagnostics": self.config.diagnostics_engine,
                "gcs": self.config.gcs_engine,
                "vision": self.config.vision_engine,
                "navigation": self.config.navigation_engine,
                "mapping": self.config.mapping_engine,
                "autonomy": self.config.autonomy_engine,
                "simulation": self.config.simulation_engine,
                "mission": self.config.mission_engine,
                "inventory": self.config.inventory_engine,
                "ai": self.config.ai_engine,
            },
            "firmware_status": self.firmware_intel.status(),
            "mavlink_status": self.mavlink.status(),
            "telemetry_ai_status": self.telemetry_ai.status(),
            "flight_log_status": self.flight_logs.status(),
            "diagnostics_status": self.diagnostics.status(),
            "mission_intel_status": self.mission_intel.status(),
            "gcs_status": self.gcs.status(),
            "visualization_status": self.visualization.status(),
            "vision_status": self.vision.status(),
            "detection_status": self.detection.status(),
            "navigation_status": self.navigation.status(),
            "mapping_status": self.mapping.status(),
            "autonomy_status": self.autonomy.status(),
            "simulation_status": self.simulation.status(),
            "bridges": {
                "platform": self.platform.health(),
                "ecosystem": self.ecosystem.health(),
            },
            "analytics": self.analytics.overview(),
        }


drone_platform = DronePlatformApplication()
