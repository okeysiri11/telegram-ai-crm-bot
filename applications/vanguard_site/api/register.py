"""Public Vanguard career-site API — not a business vertical."""

from __future__ import annotations

from aiohttp import web

from applications.recruiting_enterprise.api.middleware import json_response
from services.recruiting_ops import get_recruiting_ops_service


async def _read_json(request: web.Request) -> dict:
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _status_for(result: dict, *, created: bool = False) -> int:
    if result.get("ok") is False:
        err = result.get("error")
        if err in {"storage_unavailable", "ingest_not_configured"}:
            return 503
        if err == "validation":
            return 400
        return 400
    if result.get("duplicate"):
        return 200
    return 201 if created else 200


async def vanguard_site_apply_handler(request: web.Request) -> web.Response:
    body = await _read_json(request)
    result = await get_recruiting_ops_service().submit_vanguard_application(body)
    return json_response(result, status=_status_for(result, created=not result.get("duplicate")))


async def vanguard_site_events_handler(request: web.Request) -> web.Response:
    body = await _read_json(request)
    result = await get_recruiting_ops_service().record_vanguard_event(body)
    return json_response(result, status=_status_for(result, created=True))


async def vanguard_site_health_handler(_request: web.Request) -> web.Response:
    return json_response({"ok": True, "site": "vanguard", "path": "/vanguard", "vertical": False})


def register_vanguard_site_routes(app: web.Application) -> None:
    prefix = "/api/vanguard-site/v1"
    app.router.add_get(f"{prefix}/health", vanguard_site_health_handler)
    app.router.add_post(f"{prefix}/applications", vanguard_site_apply_handler)
    app.router.add_post(f"{prefix}/events", vanguard_site_events_handler)
