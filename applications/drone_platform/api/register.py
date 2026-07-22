from __future__ import annotations

from aiohttp import web

from applications.drone_platform.api import handlers
from applications.drone_platform.api.middleware import auth_middleware
from applications.drone_platform.config import DEFAULT_CONFIG


def register_drone_platform_routes(app: web.Application) -> None:
    """Mount Drone Platform foundation routes under /api/drone/v1."""
    prefix = DEFAULT_CONFIG.api_prefix
    app.middlewares.append(auth_middleware)

    app.router.add_get(f"{prefix}/health", handlers.health_handler)

    # registry
    app.router.add_get(f"{prefix}/registry", handlers.registry_catalog_handler)
    app.router.add_get(f"{prefix}/registry/types", handlers.registry_types_handler)
    app.router.add_get(f"{prefix}/registry/components", handlers.registry_components_handler)
    app.router.add_post(f"{prefix}/registry/components", handlers.registry_components_handler)
    app.router.add_get(f"{prefix}/registry/uavs", handlers.registry_uavs_handler)
    app.router.add_post(f"{prefix}/registry/uavs", handlers.registry_uavs_handler)

    # projects / engineering
    app.router.add_get(f"{prefix}/projects", handlers.projects_handler)
    app.router.add_post(f"{prefix}/projects", handlers.projects_handler)
    app.router.add_get(f"{prefix}/projects/{{project_id}}/versions", handlers.project_versions_handler)
    app.router.add_post(f"{prefix}/projects/{{project_id}}/versions", handlers.project_versions_handler)
    app.router.add_get(f"{prefix}/engineering/{{project_id}}", handlers.engineering_workspace_handler)
    app.router.add_get(f"{prefix}/engineering/suite", handlers.engineering_suite_status_handler)
    app.router.add_get(f"{prefix}/engineering/airframes", handlers.engineering_airframe_handler)
    app.router.add_post(f"{prefix}/engineering/airframes", handlers.engineering_airframe_handler)
    app.router.add_get(f"{prefix}/engineering/propulsion", handlers.engineering_propulsion_handler)
    app.router.add_post(f"{prefix}/engineering/propulsion", handlers.engineering_propulsion_handler)
    app.router.add_get(f"{prefix}/engineering/batteries", handlers.engineering_battery_handler)
    app.router.add_post(f"{prefix}/engineering/batteries", handlers.engineering_battery_handler)
    app.router.add_get(f"{prefix}/engineering/electronics", handlers.engineering_electronics_handler)
    app.router.add_post(f"{prefix}/engineering/electronics", handlers.engineering_electronics_handler)
    app.router.add_get(f"{prefix}/engineering/pcb", handlers.engineering_pcb_handler)
    app.router.add_post(f"{prefix}/engineering/pcb", handlers.engineering_pcb_handler)
    app.router.add_get(f"{prefix}/engineering/cad", handlers.engineering_cad_handler)
    app.router.add_post(f"{prefix}/engineering/cad", handlers.engineering_cad_handler)
    app.router.add_post(f"{prefix}/engineering/simulate", handlers.engineering_sim_handler)

    # firmware
    app.router.add_get(f"{prefix}/firmware", handlers.firmware_catalog_handler)
    app.router.add_get(f"{prefix}/firmware/projects", handlers.firmware_projects_handler)
    app.router.add_post(f"{prefix}/firmware/projects", handlers.firmware_projects_handler)
    app.router.add_post(f"{prefix}/firmware/parameters", handlers.firmware_parameters_handler)
    app.router.add_post(f"{prefix}/firmware/compare", handlers.firmware_compare_handler)
    app.router.add_get(f"{prefix}/firmware/templates", handlers.firmware_templates_handler)
    app.router.add_post(f"{prefix}/firmware/templates", handlers.firmware_templates_handler)
    app.router.add_post(f"{prefix}/firmware/export", handlers.firmware_export_handler)
    app.router.add_post(f"{prefix}/firmware/import", handlers.firmware_import_handler)
    app.router.add_post(f"{prefix}/firmware/backup", handlers.firmware_backup_handler)
    app.router.add_post(f"{prefix}/firmware/restore", handlers.firmware_restore_handler)

    # firmware intelligence 11.2
    app.router.add_get(f"{prefix}/firmware/intelligence", handlers.firmware_intel_status_handler)
    app.router.add_get(f"{prefix}/firmware/artifacts", handlers.firmware_artifacts_handler)
    app.router.add_post(f"{prefix}/firmware/artifacts", handlers.firmware_artifacts_handler)
    app.router.add_post(f"{prefix}/firmware/analyze", handlers.firmware_analyze_handler)
    app.router.add_post(f"{prefix}/firmware/build", handlers.firmware_build_handler)
    app.router.add_post(f"{prefix}/firmware/compare-artifacts", handlers.firmware_compare_artifacts_handler)
    app.router.add_post(f"{prefix}/firmware/patches", handlers.firmware_patch_handler)
    app.router.add_post(f"{prefix}/firmware/sign", handlers.firmware_sign_handler)
    app.router.add_get(f"{prefix}/firmware/releases", handlers.firmware_release_handler)
    app.router.add_post(f"{prefix}/firmware/releases", handlers.firmware_release_handler)
    app.router.add_post(f"{prefix}/firmware/rollback", handlers.firmware_rollback_handler)

    # ardupilot
    app.router.add_get(f"{prefix}/ardupilot/projects", handlers.ardupilot_projects_handler)
    app.router.add_post(f"{prefix}/ardupilot/projects", handlers.ardupilot_projects_handler)
    app.router.add_get(f"{prefix}/ardupilot/parameters", handlers.ardupilot_params_handler)
    app.router.add_get(f"{prefix}/ardupilot/modes", handlers.ardupilot_modes_handler)
    app.router.add_get(f"{prefix}/ardupilot/vehicles", handlers.ardupilot_vehicles_handler)
    app.router.add_post(f"{prefix}/ardupilot/vehicles", handlers.ardupilot_vehicles_handler)
    app.router.add_get(f"{prefix}/ardupilot/branches", handlers.ardupilot_branches_handler)
    app.router.add_post(f"{prefix}/ardupilot/branches", handlers.ardupilot_branches_handler)

    # mission planner
    app.router.add_post(f"{prefix}/mission-planner/import", handlers.mission_planner_import_handler)
    app.router.add_post(f"{prefix}/mission-planner/export", handlers.mission_planner_export_handler)
    app.router.add_post(
        f"{prefix}/mission-planner/missions/{{mission_id}}/waypoints",
        handlers.mission_planner_waypoints_handler,
    )

    # missions
    app.router.add_get(f"{prefix}/missions", handlers.missions_handler)
    app.router.add_post(f"{prefix}/missions", handlers.missions_handler)
    app.router.add_post(f"{prefix}/missions/{{mission_id}}/waypoints", handlers.mission_waypoints_handler)

    # telemetry
    app.router.add_get(f"{prefix}/telemetry/sessions", handlers.telemetry_sessions_handler)
    app.router.add_post(f"{prefix}/telemetry/sessions", handlers.telemetry_sessions_handler)
    app.router.add_post(f"{prefix}/telemetry/sessions/{{session_id}}/samples", handlers.telemetry_sample_handler)
    app.router.add_get(f"{prefix}/telemetry/ai", handlers.telemetry_ai_status_handler)
    app.router.add_post(f"{prefix}/telemetry/analyze", handlers.telemetry_analyze_handler)
    app.router.add_post(f"{prefix}/telemetry/record", handlers.telemetry_record_handler)
    app.router.add_post(f"{prefix}/telemetry/replay", handlers.telemetry_replay_handler)

    # mavlink
    app.router.add_get(f"{prefix}/mavlink", handlers.mavlink_status_handler)
    app.router.add_get(f"{prefix}/mavlink/messages", handlers.mavlink_messages_handler)
    app.router.add_get(f"{prefix}/mavlink/commands", handlers.mavlink_commands_handler)
    app.router.add_post(f"{prefix}/mavlink/parse", handlers.mavlink_parse_handler)
    app.router.add_get(f"{prefix}/mavlink/connections", handlers.mavlink_connections_handler)
    app.router.add_post(f"{prefix}/mavlink/connections", handlers.mavlink_connections_handler)
    app.router.add_post(f"{prefix}/mavlink/heartbeat", handlers.mavlink_heartbeat_handler)
    app.router.add_get(f"{prefix}/mavlink/streams", handlers.mavlink_stream_handler)
    app.router.add_post(f"{prefix}/mavlink/streams", handlers.mavlink_stream_handler)

    # flight logs / diagnostics / mission intel / gcs / visualization
    app.router.add_get(f"{prefix}/flight-logs", handlers.flight_logs_handler)
    app.router.add_post(f"{prefix}/flight-logs", handlers.flight_logs_handler)
    app.router.add_get(f"{prefix}/diagnostics", handlers.diagnostics_handler)
    app.router.add_post(f"{prefix}/diagnostics", handlers.diagnostics_handler)
    app.router.add_post(f"{prefix}/mission-intel/analyze", handlers.mission_intel_handler)
    app.router.add_post(f"{prefix}/mission-intel/compare", handlers.mission_intel_compare_handler)
    app.router.add_post(f"{prefix}/mission-intel/rth", handlers.mission_intel_rth_handler)
    app.router.add_get(f"{prefix}/gcs/bridges", handlers.gcs_bridges_handler)
    app.router.add_post(f"{prefix}/gcs/bridges", handlers.gcs_bridges_handler)
    app.router.add_post(f"{prefix}/visualization/bundle", handlers.visualization_handler)

    # vision / navigation / mapping / autonomy / simulation (11.4)
    app.router.add_get(f"{prefix}/vision", handlers.vision_status_handler)
    app.router.add_get(f"{prefix}/vision/cameras", handlers.vision_cameras_handler)
    app.router.add_post(f"{prefix}/vision/cameras", handlers.vision_cameras_handler)
    app.router.add_get(f"{prefix}/vision/streams", handlers.vision_streams_handler)
    app.router.add_post(f"{prefix}/vision/streams", handlers.vision_streams_handler)
    app.router.add_post(f"{prefix}/vision/frames", handlers.vision_frames_handler)
    app.router.add_post(f"{prefix}/vision/detect", handlers.vision_detect_handler)
    app.router.add_post(f"{prefix}/vision/track", handlers.vision_track_handler)
    app.router.add_get(f"{prefix}/navigation", handlers.navigation_status_handler)
    app.router.add_post(f"{prefix}/navigation/plan", handlers.navigation_plan_handler)
    app.router.add_get(f"{prefix}/mapping", handlers.mapping_status_handler)
    app.router.add_post(f"{prefix}/mapping/slam", handlers.mapping_slam_handler)
    app.router.add_post(f"{prefix}/mapping/mission", handlers.mapping_mission_handler)
    app.router.add_get(f"{prefix}/autonomy", handlers.autonomy_status_handler)
    app.router.add_post(f"{prefix}/autonomy/action", handlers.autonomy_action_handler)
    app.router.add_get(f"{prefix}/simulation", handlers.simulation_status_handler)
    app.router.add_get(f"{prefix}/simulation/runs", handlers.simulation_runs_handler)
    app.router.add_post(f"{prefix}/simulation/runs", handlers.simulation_runs_handler)
    app.router.add_post(f"{prefix}/simulation/scenarios", handlers.simulation_scenario_handler)

    # manufacturing suite (11.6)
    app.router.add_get(f"{prefix}/manufacturing/suite", handlers.manufacturing_suite_status_handler)
    app.router.add_get(f"{prefix}/manufacturing/orders", handlers.manufacturing_orders_handler)
    app.router.add_post(f"{prefix}/manufacturing/orders", handlers.manufacturing_orders_handler)
    app.router.add_get(f"{prefix}/manufacturing/assembly", handlers.manufacturing_assembly_handler)
    app.router.add_post(f"{prefix}/manufacturing/assembly", handlers.manufacturing_assembly_handler)
    app.router.add_get(f"{prefix}/manufacturing/bom", handlers.manufacturing_bom_handler)
    app.router.add_post(f"{prefix}/manufacturing/bom", handlers.manufacturing_bom_handler)
    app.router.add_get(f"{prefix}/manufacturing/warehouse", handlers.manufacturing_warehouse_handler)
    app.router.add_post(f"{prefix}/manufacturing/warehouse", handlers.manufacturing_warehouse_handler)
    app.router.add_post(f"{prefix}/manufacturing/workflow", handlers.manufacturing_workflow_handler)
    app.router.add_post(f"{prefix}/manufacturing/programming", handlers.manufacturing_programming_handler)
    app.router.add_post(f"{prefix}/manufacturing/calibration", handlers.manufacturing_calibration_handler)
    app.router.add_post(f"{prefix}/manufacturing/qa", handlers.manufacturing_qa_handler)
    app.router.add_post(f"{prefix}/manufacturing/flight-tests", handlers.manufacturing_flight_tests_handler)
    app.router.add_get(f"{prefix}/manufacturing/lifecycle", handlers.manufacturing_lifecycle_handler)
    app.router.add_post(f"{prefix}/manufacturing/lifecycle", handlers.manufacturing_lifecycle_handler)

    # inventory
    app.router.add_get(f"{prefix}/inventory/warehouses", handlers.inventory_warehouses_handler)
    app.router.add_post(f"{prefix}/inventory/warehouses", handlers.inventory_warehouses_handler)
    app.router.add_get(f"{prefix}/inventory/suppliers", handlers.inventory_suppliers_handler)
    app.router.add_post(f"{prefix}/inventory/suppliers", handlers.inventory_suppliers_handler)
    app.router.add_get(f"{prefix}/inventory/stock", handlers.inventory_stock_handler)
    app.router.add_post(f"{prefix}/inventory/stock", handlers.inventory_stock_handler)
    app.router.add_post(f"{prefix}/inventory/reservations", handlers.inventory_reserve_handler)
    app.router.add_get(f"{prefix}/inventory/purchase-orders", handlers.inventory_purchase_handler)
    app.router.add_post(f"{prefix}/inventory/purchase-orders", handlers.inventory_purchase_handler)

    # documentation
    app.router.add_get(f"{prefix}/documentation", handlers.documentation_handler)
    app.router.add_post(f"{prefix}/documentation", handlers.documentation_handler)

    # ai
    app.router.add_get(f"{prefix}/ai", handlers.ai_capabilities_handler)
    app.router.add_post(f"{prefix}/ai/assist", handlers.ai_assist_handler)
