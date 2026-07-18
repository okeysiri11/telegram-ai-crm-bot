# Admin assignment statistics REST routes — /api/v1/assignment/statistics

from __future__ import annotations

import logging

from aiohttp import web

logger = logging.getLogger(__name__)


async def assignment_statistics_handler(request: web.Request) -> web.Response:
    from services.smart_assignment_service import smart_assignment_service

    stats = await smart_assignment_service.get_statistics()
    return web.json_response(stats)


def register_assignment_admin_routes(app: web.Application) -> None:
    app.router.add_get("/api/v1/assignment/statistics", assignment_statistics_handler)
    logger.info("assignment_admin_routes_registered")
