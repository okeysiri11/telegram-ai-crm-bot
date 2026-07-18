# Admin workflow REST routes — /api/v1/workflows

from __future__ import annotations

import logging

from aiohttp import web

logger = logging.getLogger(__name__)


async def workflows_dashboard_handler(request: web.Request) -> web.Response:
    from workflow import workflow_engine

    stats = await workflow_engine.get_statistics()
    return web.json_response(stats)


def register_workflow_admin_routes(app: web.Application) -> None:
    app.router.add_get("/api/v1/workflows", workflows_dashboard_handler)
    logger.info("workflow_admin_routes_registered")
