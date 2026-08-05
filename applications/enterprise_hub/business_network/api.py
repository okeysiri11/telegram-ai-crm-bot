"""API handlers — Enterprise Business Network (Sprint 29.0)."""

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
    return enterprise_hub.business_network


async def ebn_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "version": "29.0",
            "service": "enterprise-ebn",
            "application_version": health.get("application_version"),
            "business_network_ready": health.get("business_network_ready", True),
            "suite": _suite().status(),
        }
    )


async def ebn_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ebn_inventory_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().inventory())
    except Exception as exc:
        return _handle_error(exc)


async def ebn_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def ebn_profiles_handler(request: web.Request) -> web.Response:
    try:
        _suite().seed()
        return json_response(
            {"profiles": [p.to_dict() for p in _suite().graph.profiles.values()]}
        )
    except Exception as exc:
        return _handle_error(exc)


async def ebn_profile_handler(request: web.Request) -> web.Response:
    try:
        _suite().seed()
        profile_id = request.match_info["profile_id"]
        profile = _suite().graph.profiles.get(profile_id)
        if not profile:
            raise NotFoundError("profile_not_found")
        return json_response({"profile": profile.to_dict()})
    except Exception as exc:
        return _handle_error(exc)


async def ebn_relationships_handler(request: web.Request) -> web.Response:
    try:
        _suite().seed()
        if request.method == "POST":
            body = await request.json()
            frm = body.get("fromProfileId") or body.get("from_profile_id")
            to = body.get("toProfileId") or body.get("to_profile_id")
            rel_type = body.get("type") or "partner"
            if not frm or not to:
                raise ValidationError("fromProfileId and toProfileId are required")
            rel = _suite().graph.create_relationship(frm, to, rel_type)
            return json_response({"ok": True, "relationship": rel.to_dict()}, status=201)
        return json_response(
            {"relationships": [r.to_dict() for r in _suite().graph.relationships.values()]}
        )
    except Exception as exc:
        return _handle_error(exc)


async def ebn_approve_handler(request: web.Request) -> web.Response:
    try:
        rel_id = request.match_info["relationship_id"]
        rel = _suite().graph.approve(rel_id)
        if not rel:
            raise NotFoundError("relationship_not_found")
        return json_response({"relationship": rel.to_dict()})
    except Exception as exc:
        return _handle_error(exc)


async def ebn_reject_handler(request: web.Request) -> web.Response:
    try:
        rel_id = request.match_info["relationship_id"]
        rel = _suite().graph.reject(rel_id)
        if not rel:
            raise NotFoundError("relationship_not_found")
        return json_response({"relationship": rel.to_dict()})
    except Exception as exc:
        return _handle_error(exc)


async def ebn_graph_handler(request: web.Request) -> web.Response:
    try:
        _suite().seed()
        profile_id = request.rel_url.query.get("profileId")
        if profile_id:
            return json_response(_suite().graph.connections(profile_id))
        return json_response(_suite().graph.snapshot())
    except Exception as exc:
        return _handle_error(exc)


async def ebn_city_handler(request: web.Request) -> web.Response:
    try:
        _suite().seed()
        profile_id = request.match_info["profile_id"]
        facade = _suite().graph.city_facade(profile_id)
        if not facade:
            raise NotFoundError("profile_not_found")
        return json_response({"facade": facade})
    except Exception as exc:
        return _handle_error(exc)
