# Drone Platform configuration — Sprint 11.7 Mission Operations & Fleet Command.

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DronePlatformConfig:
    application_name: str = "Drone Platform"
    application: str = "drone_platform"
    application_version: str = "1.6.0-alpha"
    release_status: str = "Mission Operations Alpha"
    api_version: str = "v1"
    api_prefix: str = "/api/drone/v1"
    internal_prefix: str = "/internal/drone/v1"
    platform_dependency: str = "AI Platform Core v3"
    ecosystem_dependency: str = "AI Ecosystem v1.5"
    registry_engine: str = "1.0"
    engineering_engine: str = "1.1"
    engineering_suite: str = "1.0"
    manufacturing_engine: str = "1.1"
    manufacturing_suite: str = "1.0"
    mission_operations: str = "1.0"
    fleet_command: str = "1.0"
    swarm_intelligence: str = "1.0"
    firmware_engine: str = "1.1"
    firmware_intelligence: str = "1.0"
    ardupilot_engine: str = "1.0"
    mission_planner_bridge: str = "1.0"
    mavlink_engine: str = "1.0"
    telemetry_ai_engine: str = "1.0"
    flight_log_engine: str = "1.0"
    mission_intelligence_engine: str = "1.0"
    diagnostics_engine: str = "1.0"
    gcs_engine: str = "1.1"
    vision_engine: str = "1.0"
    navigation_engine: str = "1.0"
    mapping_engine: str = "1.0"
    autonomy_engine: str = "1.0"
    simulation_engine: str = "1.1"
    mission_engine: str = "1.2"
    inventory_engine: str = "1.1"
    ai_engine: str = "1.6"


DEFAULT_CONFIG = DronePlatformConfig()
