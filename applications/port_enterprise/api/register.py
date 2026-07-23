"""Register Port Enterprise routes (Sprint 15.0)."""

from __future__ import annotations

from aiohttp import web

from applications.port_enterprise.api import container_handlers, handlers, navigation_handlers
from applications.port_enterprise.api.middleware import auth_middleware
from applications.port_enterprise.config import DEFAULT_CONFIG


def register_port_enterprise_routes(app: web.Application) -> None:
    prefix = DEFAULT_CONFIG.api_prefix
    if auth_middleware not in app.middlewares:
        app.middlewares.append(auth_middleware)

    app.router.add_get(f"{prefix}/health", handlers.health_handler)
    app.router.add_post(f"{prefix}/bootstrap", handlers.bootstrap_handler)
    app.router.add_get(f"{prefix}/ports", handlers.ports_handler)
    app.router.add_post(f"{prefix}/ports", handlers.ports_handler)
    app.router.add_get(f"{prefix}/terminals", handlers.terminals_handler)
    app.router.add_post(f"{prefix}/terminals", handlers.terminals_handler)
    app.router.add_get(f"{prefix}/cargo", handlers.cargo_handler)
    app.router.add_post(f"{prefix}/cargo", handlers.cargo_handler)
    app.router.add_get(f"{prefix}/shipping", handlers.shipping_handler)
    app.router.add_post(f"{prefix}/shipping", handlers.shipping_handler)
    app.router.add_get(f"{prefix}/fleet", handlers.fleet_handler)
    app.router.add_post(f"{prefix}/fleet", handlers.fleet_handler)
    app.router.add_get(f"{prefix}/operations", handlers.operations_handler)
    app.router.add_post(f"{prefix}/operations", handlers.operations_handler)
    app.router.add_get(f"{prefix}/dashboard", handlers.dashboard_handler)
    app.router.add_post(f"{prefix}/dashboard", handlers.dashboard_handler)
    app.router.add_get(f"{prefix}/knowledge", handlers.knowledge_handler)
    app.router.add_post(f"{prefix}/knowledge", handlers.knowledge_handler)

    # Sprint 15.1 — Navigation / VTS (additive; prior routes unchanged)
    nav = DEFAULT_CONFIG.navigation_api_prefix
    app.router.add_get(f"{nav}/health", navigation_handlers.nav_health_handler)
    app.router.add_post(f"{nav}/bootstrap", navigation_handlers.nav_bootstrap_handler)
    app.router.add_get(f"{nav}/vts", navigation_handlers.nav_vts_handler)
    app.router.add_post(f"{nav}/vts", navigation_handlers.nav_vts_handler)
    app.router.add_get(f"{nav}/ais", navigation_handlers.nav_ais_handler)
    app.router.add_post(f"{nav}/ais", navigation_handlers.nav_ais_handler)
    app.router.add_get(f"{nav}/radar", navigation_handlers.nav_radar_handler)
    app.router.add_post(f"{nav}/radar", navigation_handlers.nav_radar_handler)
    app.router.add_get(f"{nav}/navigation", navigation_handlers.nav_navigation_handler)
    app.router.add_post(f"{nav}/navigation", navigation_handlers.nav_navigation_handler)
    app.router.add_get(f"{nav}/safety", navigation_handlers.nav_safety_handler)
    app.router.add_post(f"{nav}/safety", navigation_handlers.nav_safety_handler)
    app.router.add_get(f"{nav}/ai", navigation_handlers.nav_ai_handler)
    app.router.add_post(f"{nav}/ai", navigation_handlers.nav_ai_handler)
    app.router.add_get(f"{nav}/dashboard", navigation_handlers.nav_dashboard_handler)
    app.router.add_post(f"{nav}/dashboard", navigation_handlers.nav_dashboard_handler)
    app.router.add_get(f"{nav}/knowledge", navigation_handlers.nav_knowledge_handler)
    app.router.add_post(f"{nav}/knowledge", navigation_handlers.nav_knowledge_handler)

    # Sprint 15.2 — Container Management (additive; prior routes unchanged)
    cm = DEFAULT_CONFIG.container_management_api_prefix
    app.router.add_get(f"{cm}/health", container_handlers.cm_health_handler)
    app.router.add_post(f"{cm}/bootstrap", container_handlers.cm_bootstrap_handler)
    app.router.add_get(f"{cm}/containers", container_handlers.cm_containers_handler)
    app.router.add_post(f"{cm}/containers", container_handlers.cm_containers_handler)
    app.router.add_get(f"{cm}/operations", container_handlers.cm_operations_handler)
    app.router.add_post(f"{cm}/operations", container_handlers.cm_operations_handler)
    app.router.add_get(f"{cm}/yard", container_handlers.cm_yard_handler)
    app.router.add_post(f"{cm}/yard", container_handlers.cm_yard_handler)
    app.router.add_get(f"{cm}/equipment", container_handlers.cm_equipment_handler)
    app.router.add_post(f"{cm}/equipment", container_handlers.cm_equipment_handler)
    app.router.add_get(f"{cm}/automation", container_handlers.cm_automation_handler)
    app.router.add_post(f"{cm}/automation", container_handlers.cm_automation_handler)
    app.router.add_get(f"{cm}/twin", container_handlers.cm_twin_handler)
    app.router.add_post(f"{cm}/twin", container_handlers.cm_twin_handler)
    app.router.add_get(f"{cm}/dashboard", container_handlers.cm_dashboard_handler)
    app.router.add_post(f"{cm}/dashboard", container_handlers.cm_dashboard_handler)
    app.router.add_get(f"{cm}/knowledge", container_handlers.cm_knowledge_handler)
    app.router.add_post(f"{cm}/knowledge", container_handlers.cm_knowledge_handler)
