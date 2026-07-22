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

    # missions
    app.router.add_get(f"{prefix}/missions", handlers.missions_handler)
    app.router.add_post(f"{prefix}/missions", handlers.missions_handler)
    app.router.add_post(f"{prefix}/missions/{{mission_id}}/waypoints", handlers.mission_waypoints_handler)

    # telemetry
    app.router.add_get(f"{prefix}/telemetry/sessions", handlers.telemetry_sessions_handler)
    app.router.add_post(f"{prefix}/telemetry/sessions", handlers.telemetry_sessions_handler)
    app.router.add_post(f"{prefix}/telemetry/sessions/{{session_id}}/samples", handlers.telemetry_sample_handler)

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
