"""Register Agro Enterprise routes (Sprint 14.0 + 14.1)."""

from __future__ import annotations

from aiohttp import web

from applications.agro_enterprise.api import handlers, irrigation_handlers, precision_handlers
from applications.agro_enterprise.api.middleware import auth_middleware
from applications.agro_enterprise.config import DEFAULT_CONFIG


def register_agro_enterprise_routes(app: web.Application) -> None:
    prefix = DEFAULT_CONFIG.api_prefix
    if auth_middleware not in app.middlewares:
        app.middlewares.append(auth_middleware)

    app.router.add_get(f"{prefix}/health", handlers.health_handler)
    app.router.add_post(f"{prefix}/bootstrap", handlers.bootstrap_handler)
    app.router.add_get(f"{prefix}/marketplace", handlers.marketplace_handler)
    app.router.add_post(f"{prefix}/marketplace", handlers.marketplace_handler)
    app.router.add_get(f"{prefix}/farms", handlers.farms_handler)
    app.router.add_post(f"{prefix}/farms", handlers.farms_handler)
    app.router.add_get(f"{prefix}/crops", handlers.crops_handler)
    app.router.add_post(f"{prefix}/crops", handlers.crops_handler)
    app.router.add_get(f"{prefix}/crm", handlers.crm_handler)
    app.router.add_post(f"{prefix}/crm", handlers.crm_handler)
    app.router.add_get(f"{prefix}/knowledge", handlers.knowledge_handler)
    app.router.add_post(f"{prefix}/knowledge", handlers.knowledge_handler)
    app.router.add_get(f"{prefix}/dashboard", handlers.dashboard_handler)
    app.router.add_post(f"{prefix}/dashboard", handlers.dashboard_handler)

    # Sprint 14.1 — Precision Agriculture (additive)
    pa = DEFAULT_CONFIG.precision_agriculture_api_prefix
    app.router.add_get(f"{pa}/health", precision_handlers.pa_health_handler)
    app.router.add_post(f"{pa}/bootstrap", precision_handlers.pa_bootstrap_handler)
    app.router.add_get(f"{pa}/fields", precision_handlers.pa_fields_handler)
    app.router.add_post(f"{pa}/fields", precision_handlers.pa_fields_handler)
    app.router.add_get(f"{pa}/gis", precision_handlers.pa_gis_handler)
    app.router.add_post(f"{pa}/gis", precision_handlers.pa_gis_handler)
    app.router.add_get(f"{pa}/drone", precision_handlers.pa_drone_handler)
    app.router.add_post(f"{pa}/drone", precision_handlers.pa_drone_handler)
    app.router.add_get(f"{pa}/satellite", precision_handlers.pa_satellite_handler)
    app.router.add_post(f"{pa}/satellite", precision_handlers.pa_satellite_handler)
    app.router.add_get(f"{pa}/iot", precision_handlers.pa_iot_handler)
    app.router.add_post(f"{pa}/iot", precision_handlers.pa_iot_handler)
    app.router.add_get(f"{pa}/ai", precision_handlers.pa_ai_handler)
    app.router.add_post(f"{pa}/ai", precision_handlers.pa_ai_handler)
    app.router.add_get(f"{pa}/dashboard", precision_handlers.pa_dashboard_handler)
    app.router.add_post(f"{pa}/dashboard", precision_handlers.pa_dashboard_handler)
    app.router.add_get(f"{pa}/knowledge", precision_handlers.pa_knowledge_handler)
    app.router.add_post(f"{pa}/knowledge", precision_handlers.pa_knowledge_handler)

    # Sprint 14.2 — Smart Irrigation (additive; prior sprint routes unchanged)
    si = DEFAULT_CONFIG.smart_irrigation_api_prefix
    app.router.add_get(f"{si}/health", irrigation_handlers.si_health_handler)
    app.router.add_post(f"{si}/bootstrap", irrigation_handlers.si_bootstrap_handler)
    app.router.add_get(f"{si}/soil", irrigation_handlers.si_soil_handler)
    app.router.add_post(f"{si}/soil", irrigation_handlers.si_soil_handler)
    app.router.add_get(f"{si}/water", irrigation_handlers.si_water_handler)
    app.router.add_post(f"{si}/water", irrigation_handlers.si_water_handler)
    app.router.add_get(f"{si}/irrigation", irrigation_handlers.si_irrigation_handler)
    app.router.add_post(f"{si}/irrigation", irrigation_handlers.si_irrigation_handler)
    app.router.add_get(f"{si}/iot", irrigation_handlers.si_iot_handler)
    app.router.add_post(f"{si}/iot", irrigation_handlers.si_iot_handler)
    app.router.add_get(f"{si}/ai", irrigation_handlers.si_ai_handler)
    app.router.add_post(f"{si}/ai", irrigation_handlers.si_ai_handler)
    app.router.add_get(f"{si}/environment", irrigation_handlers.si_environment_handler)
    app.router.add_post(f"{si}/environment", irrigation_handlers.si_environment_handler)
    app.router.add_get(f"{si}/dashboard", irrigation_handlers.si_dashboard_handler)
    app.router.add_post(f"{si}/dashboard", irrigation_handlers.si_dashboard_handler)
    app.router.add_get(f"{si}/knowledge", irrigation_handlers.si_knowledge_handler)
    app.router.add_post(f"{si}/knowledge", irrigation_handlers.si_knowledge_handler)
