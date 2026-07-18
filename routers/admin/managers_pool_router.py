# Admin manager pool REST routes — /api/v1/managers/pool

from __future__ import annotations

import logging

from aiohttp import web

logger = logging.getLogger(__name__)


async def managers_pool_handler(request: web.Request) -> web.Response:
    from services.manager_pool_service import manager_pool_service

    vertical = request.query.get("vertical")
    payload = await manager_pool_service.get_pool_dashboard(vertical=vertical)
    return web.json_response(payload)


def register_managers_pool_routes(app: web.Application) -> None:
    app.router.add_get("/api/v1/managers/pool", managers_pool_handler)
    logger.info("managers_pool_routes_registered")
