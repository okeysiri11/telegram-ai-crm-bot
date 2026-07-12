# HTTP API — system endpoints (health checks, future REST layer).

from aiohttp import web

from database.session import check_db_health


async def db_health_handler(request: web.Request) -> web.Response:
    result = await check_db_health()
    status_code = 200 if result.get("ok") else 503
    return web.json_response(result, status=status_code)


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/system/db-health", db_health_handler)
    return app


async def start_api_server(host: str = "0.0.0.0", port: int = 8080) -> web.AppRunner:
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    return runner
