# HTTP API — system endpoints and Public API Gateway v1.

from aiohttp import web

from api.handlers import (
    ai_advertising_agent_feature_handler,
    ai_advertising_agent_handler,
    ai_procurement_agent_feature_handler,
    ai_procurement_agent_handler,
    ai_sales_agent_feature_handler,
    ai_sales_agent_handler,
    api_info_handler,
    auth_token_handler,
    dealer_portal_handler,
    dealer_portal_module_handler,
    lead_marketplace_handler,
    lead_marketplace_feature_handler,
    recommendation_engine_feature_handler,
    recommendation_engine_handler,
    communication_hub_feature_handler,
    communication_hub_handler,
    ai_conversation_skills_feature_handler,
    ai_conversation_skills_handler,
    deal_pipeline_feature_handler,
    deal_pipeline_handler,
    cross_posting_feature_handler,
    cross_posting_handler,
    analytics_feature_handler,
    analytics_handler,
    deals_create_handler,
    deals_list_handler,
    documents_create_handler,
    documents_list_handler,
    fx_rates_handler,
    inventory_list_handler,
    notifications_create_handler,
    notifications_list_handler,
    orders_create_handler,
    orders_list_handler,
    partners_create_handler,
    partners_list_handler,
    pricing_calculate_handler,
    vehicles_create_handler,
    vehicles_list_handler,
)
from database.session import check_db_health
from api.health_handlers import health_handler, liveness_handler, readiness_handler


async def db_health_handler(request: web.Request) -> web.Response:
    result = await check_db_health()
    status_code = 200 if result.get("ok") else 503
    return web.json_response(result, status=status_code)


def create_app() -> web.Application:
    from api.crm_api import register_crm_api_routes
    from services.observability import metrics_handler, prometheus_middleware

    app = web.Application(middlewares=[prometheus_middleware])

    # System / production readiness
    app.router.add_get("/liveness", liveness_handler)
    app.router.add_get("/readiness", readiness_handler)
    app.router.add_get("/health", health_handler)
    app.router.add_get("/system/db-health", db_health_handler)
    app.router.add_get("/metrics", metrics_handler)

    # CRM Marketplace REST API (/api/*)
    register_crm_api_routes(app)

    # Gateway info
    app.router.add_get("/v1", api_info_handler)
    app.router.add_get("/v1/", api_info_handler)

    # Auth
    app.router.add_post("/v1/auth/token", auth_token_handler)

    # Domain endpoints
    app.router.add_get("/v1/deals", deals_list_handler)
    app.router.add_post("/v1/deals", deals_create_handler)

    app.router.add_get("/v1/partners", partners_list_handler)
    app.router.add_post("/v1/partners", partners_create_handler)

    app.router.add_post("/v1/pricing/calculate", pricing_calculate_handler)

    app.router.add_get("/v1/fx/rates", fx_rates_handler)

    app.router.add_get("/v1/vehicles", vehicles_list_handler)
    app.router.add_post("/v1/vehicles", vehicles_create_handler)

    app.router.add_get("/v1/inventory", inventory_list_handler)

    app.router.add_get("/v1/orders", orders_list_handler)
    app.router.add_post("/v1/orders", orders_create_handler)

    app.router.add_get("/v1/documents", documents_list_handler)
    app.router.add_post("/v1/documents", documents_create_handler)

    app.router.add_get("/v1/notifications", notifications_list_handler)
    app.router.add_post("/v1/notifications", notifications_create_handler)

    app.router.add_get("/v1/dealer-portal", dealer_portal_handler)
    app.router.add_get("/v1/dealer-portal/modules/{module}", dealer_portal_module_handler)

    app.router.add_get("/v1/lead-marketplace", lead_marketplace_handler)
    app.router.add_get("/v1/lead-marketplace/features/{feature}", lead_marketplace_feature_handler)

    app.router.add_get("/v1/ai-procurement-agent", ai_procurement_agent_handler)
    app.router.add_get(
        "/v1/ai-procurement-agent/features/{feature}",
        ai_procurement_agent_feature_handler,
    )

    app.router.add_get("/v1/ai-advertising-agent", ai_advertising_agent_handler)
    app.router.add_get(
        "/v1/ai-advertising-agent/features/{feature}",
        ai_advertising_agent_feature_handler,
    )

    app.router.add_get("/v1/ai-sales-agent", ai_sales_agent_handler)
    app.router.add_get(
        "/v1/ai-sales-agent/features/{feature}",
        ai_sales_agent_feature_handler,
    )

    app.router.add_get("/v1/recommendation-engine", recommendation_engine_handler)
    app.router.add_get(
        "/v1/recommendation-engine/features/{feature}",
        recommendation_engine_feature_handler,
    )

    app.router.add_get("/v1/communication-hub", communication_hub_handler)
    app.router.add_get(
        "/v1/communication-hub/features/{feature}",
        communication_hub_feature_handler,
    )

    app.router.add_get("/v1/ai-conversation-skills", ai_conversation_skills_handler)
    app.router.add_get(
        "/v1/ai-conversation-skills/features/{feature}",
        ai_conversation_skills_feature_handler,
    )

    app.router.add_get("/v1/deal-pipeline", deal_pipeline_handler)
    app.router.add_get(
        "/v1/deal-pipeline/features/{feature}",
        deal_pipeline_feature_handler,
    )

    app.router.add_get("/v1/cross-posting", cross_posting_handler)
    app.router.add_get(
        "/v1/cross-posting/features/{feature}",
        cross_posting_feature_handler,
    )

    app.router.add_get("/v1/analytics", analytics_handler)
    app.router.add_get(
        "/v1/analytics/features/{feature}",
        analytics_feature_handler,
    )

    from routers.admin.sla_router import register_sla_admin_routes
    from routers.admin.managers_pool_router import register_managers_pool_routes
    from routers.admin.assignment_router import register_assignment_admin_routes
    from routers.admin.workflow_router import register_workflow_admin_routes
    from routers.admin.platform_sdk_router import register_platform_sdk_routes
    from routers.admin.configuration_router import register_configuration_admin_routes

    register_sla_admin_routes(app)
    register_managers_pool_routes(app)
    register_assignment_admin_routes(app)
    register_workflow_admin_routes(app)
    register_platform_sdk_routes(app)
    register_configuration_admin_routes(app)

    return app


async def start_api_server(host: str = "0.0.0.0", port: int = 8080) -> web.AppRunner | None:
    import logging

    logger = logging.getLogger(__name__)
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    try:
        await site.start()
    except OSError as exc:
        await runner.cleanup()
        logger.warning(
            "API server not started on %s:%s (%s). Bot polling will continue.",
            host,
            port,
            exc,
        )
        return None
    return runner
