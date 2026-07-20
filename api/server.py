# HTTP API — system endpoints and Public API Gateway v1.

from aiohttp import web

from api.health_handlers import health_handler, liveness_handler, readiness_handler
from database.session import check_db_health


async def db_health_handler(request: web.Request) -> web.Response:
    result = await check_db_health()
    status_code = 200 if result.get("ok") else 503
    return web.json_response(result, status=status_code)


def create_app() -> web.Application:
    from api.crm_api import register_crm_api_routes
    from api.v1 import register_api_v1_routes
    from services.observability import metrics_handler, prometheus_middleware

    app = web.Application(middlewares=[prometheus_middleware])

    # System / production readiness
    app.router.add_get("/liveness", liveness_handler)
    app.router.add_get("/readiness", readiness_handler)
    app.router.add_get("/health", health_handler)
    app.router.add_get("/system/db-health", db_health_handler)
    app.router.add_get("/metrics", metrics_handler)

    # CRM Marketplace REST API (/api/*) — legacy, unversioned
    register_crm_api_routes(app)

    # Frozen public API v1 (/api/v1/*) with legacy /v1/* compatibility adapters
    register_api_v1_routes(app)

    from platform_management.management_router import register_management_routes

    register_management_routes(app)

    from applications.auto_marketplace.api.register import register_auto_marketplace_routes

    register_auto_marketplace_routes(app)

    async def _init_plugins(_app: web.Application) -> None:
        from platform_plugins.plugin_manager import plugin_manager

        await plugin_manager.initialize(app=_app, auto_enable=False)

    app.on_startup.append(_init_plugins)

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
