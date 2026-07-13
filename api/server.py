# HTTP API — system endpoints and Public API Gateway v1.

from aiohttp import web

from api.handlers import (
    api_info_handler,
    auth_token_handler,
    dealer_portal_handler,
    dealer_portal_module_handler,
    lead_marketplace_handler,
    lead_marketplace_feature_handler,
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


async def db_health_handler(request: web.Request) -> web.Response:
    result = await check_db_health()
    status_code = 200 if result.get("ok") else 503
    return web.json_response(result, status=status_code)


def create_app() -> web.Application:
    app = web.Application()

    # System
    app.router.add_get("/system/db-health", db_health_handler)

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

    return app


async def start_api_server(host: str = "0.0.0.0", port: int = 8080) -> web.AppRunner:
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    return runner
