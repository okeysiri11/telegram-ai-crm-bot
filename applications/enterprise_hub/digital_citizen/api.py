"""API handlers — Enterprise Digital Citizen (Sprint 29.1)."""

from __future__ import annotations

from aiohttp import web

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.middleware import json_response
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError


def _handle_error(exc: Exception) -> web.Response:
    if isinstance(exc, NotFoundError):
        return json_response({"error": str(exc)}, status=404)
    if isinstance(exc, ValidationError):
        return json_response({"error": str(exc)}, status=400)
    return json_response({"error": str(exc)}, status=500)


def _suite():
    return enterprise_hub.digital_citizen


async def edc_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "version": "29.1",
            "service": "enterprise-edc",
            "application_version": health.get("application_version"),
            "digital_citizen_ready": health.get("digital_citizen_ready", True),
            "suite": _suite().status(),
        }
    )


async def edc_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def edc_inventory_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().inventory())
    except Exception as exc:
        return _handle_error(exc)


async def edc_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def edc_citizens_handler(request: web.Request) -> web.Response:
    try:
        _suite().seed()
        return json_response({"citizens": [c.to_dict() for c in _suite().citizens.values()]})
    except Exception as exc:
        return _handle_error(exc)


async def edc_citizen_handler(request: web.Request) -> web.Response:
    try:
        _suite().seed()
        cid = request.match_info["citizen_id"]
        c = _suite().citizens.get(cid)
        if not c:
            raise NotFoundError("citizen_not_found")
        return json_response({"citizen": c.to_dict()})
    except Exception as exc:
        return _handle_error(exc)


async def edc_memberships_handler(request: web.Request) -> web.Response:
    try:
        _suite().seed()
        citizen_id = request.rel_url.query.get("citizenId")
        items = list(_suite().memberships.values())
        if citizen_id:
            items = [m for m in items if m.citizen_id == citizen_id]
        return json_response({"memberships": [m.to_dict() for m in items]})
    except Exception as exc:
        return _handle_error(exc)


async def edc_presence_handler(request: web.Request) -> web.Response:
    try:
        _suite().seed()
        if request.method == "POST":
            body = await request.json()
            cid = body.get("citizenId") or body.get("citizen_id")
            status = body.get("status")
            if not cid or not status:
                raise ValidationError("citizenId and status required")
            c = _suite().set_presence(cid, status)
            if not c:
                raise NotFoundError("citizen_not_found")
            return json_response({"ok": True, "citizen": c.to_dict()})
        return json_response(
            {
                "presence": [
                    {
                        "citizenId": c.id,
                        "displayName": c.display_name,
                        "status": c.presence,
                        "officeId": c.office_id,
                        "cityBuildingId": c.city_building_id,
                    }
                    for c in _suite().citizens.values()
                ]
            }
        )
    except Exception as exc:
        return _handle_error(exc)


async def edc_city_handler(request: web.Request) -> web.Response:
    try:
        _suite().seed()
        cid = request.match_info["citizen_id"]
        facade = _suite().city_facade(cid)
        if not facade:
            raise NotFoundError("citizen_not_found")
        return json_response({"facade": facade})
    except Exception as exc:
        return _handle_error(exc)
