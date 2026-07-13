# Production Readiness Suite — HTTP health endpoints.

from __future__ import annotations

from aiohttp import web

from services.production_readiness_suite import ProductionReadinessSuite


async def liveness_handler(request: web.Request) -> web.Response:
    payload = await ProductionReadinessSuite.liveness()
    return web.json_response(payload, status=200)


async def readiness_handler(request: web.Request) -> web.Response:
    payload = await ProductionReadinessSuite.readiness()
    status_code = 200 if payload.get("ready") else 503
    return web.json_response(payload, status=status_code)


async def health_handler(request: web.Request) -> web.Response:
    payload = await ProductionReadinessSuite.health()
    status_code = 200 if payload.get("ok") else 503
    return web.json_response(payload, status=status_code)
