# Admin SLA dashboard REST routes — /api/v1/sla/*

from __future__ import annotations

import logging

from aiohttp import web

logger = logging.getLogger(__name__)


async def sla_overdue_handler(request: web.Request) -> web.Response:
    from services.sla_dashboard_service import sla_dashboard_service

    try:
        limit = int(request.query.get("limit", "100"))
    except ValueError:
        limit = 100
    limit = max(1, min(limit, 500))

    items = await sla_dashboard_service.get_overdue(limit=limit)
    return web.json_response(items)


async def sla_risk_handler(request: web.Request) -> web.Response:
    from services.sla_dashboard_service import sla_dashboard_service

    try:
        limit = int(request.query.get("limit", "100"))
    except ValueError:
        limit = 100
    limit = max(1, min(limit, 500))

    items = await sla_dashboard_service.get_at_risk(limit=limit)
    return web.json_response(items)


async def sla_statistics_handler(request: web.Request) -> web.Response:
    from services.sla_dashboard_service import sla_dashboard_service

    stats = await sla_dashboard_service.get_statistics()
    return web.json_response(stats)


async def sla_owner_escalated_handler(request: web.Request) -> web.Response:
    from services.sla_dashboard_service import sla_dashboard_service

    try:
        limit = int(request.query.get("limit", "100"))
    except ValueError:
        limit = 100
    limit = max(1, min(limit, 500))

    items = await sla_dashboard_service.get_owner_escalated(limit=limit)
    return web.json_response(items)


def register_sla_admin_routes(app: web.Application) -> None:
    app.router.add_get("/api/v1/sla/overdue", sla_overdue_handler)
    app.router.add_get("/api/v1/sla/risk", sla_risk_handler)
    app.router.add_get("/api/v1/sla/statistics", sla_statistics_handler)
    app.router.add_get("/api/v1/sla/owner-escalated", sla_owner_escalated_handler)
    logger.info("sla_admin_routes_registered")
