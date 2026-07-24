"""API handlers — Enterprise Business Capability Platform (Sprint 20.11)."""

from __future__ import annotations

from aiohttp import web

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.middleware import json_response
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError


async def _read_json(request: web.Request) -> dict:
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _handle_error(exc: Exception) -> web.Response:
    if isinstance(exc, NotFoundError):
        return json_response({"error": str(exc)}, status=404)
    if isinstance(exc, ValidationError):
        return json_response({"error": str(exc)}, status=400)
    return json_response({"error": str(exc)}, status=500)


def _suite():
    return enterprise_hub.business_capabilities


async def ebc_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "business_capabilities_ready": health.get("business_capabilities_ready"),
            "capability_registry_ready": health.get("capability_registry_ready"),
            "maturity_engine_ready": health.get("maturity_engine_ready"),
            "capability_roadmap_ready": health.get("capability_roadmap_ready"),
            "suite": _suite().status(),
        }
    )


async def ebc_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ebc_capabilities_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response({**suite.registry.status(), "items": suite.registry.list_all()})
        body = await _read_json(request)
        created = suite.registry.register(
            key=body.get("key", ""),
            name=body.get("name", ""),
            domain=body.get("domain", "custom"),
            owner=body.get("owner", "system"),
            description=body.get("description", ""),
            strategic_goal=body.get("strategic_goal", ""),
            maturity_level=int(body.get("maturity_level", 1) or 1),
            parent_key=body.get("parent_key"),
            kpi=body.get("kpi") if isinstance(body.get("kpi"), list) else None,
            processes=body.get("processes") if isinstance(body.get("processes"), list) else None,
            ai_components=body.get("ai_components") if isinstance(body.get("ai_components"), list) else None,
            digital_twin_ref=body.get("digital_twin_ref"),
            status=body.get("status", "active"),
        )
        return json_response(created, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ebc_hierarchy_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        root = body.get("root_key") or request.rel_url.query.get("root_key", "enterprise")
        return json_response(_suite().mapper.hierarchy(root_key=root))
    except Exception as exc:
        return _handle_error(exc)


async def ebc_dependencies_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response(suite.dependencies.graph())
        body = await _read_json(request)
        return json_response(
            suite.dependencies.link(
                source_key=body.get("source_key", ""),
                target_key=body.get("target_key", ""),
                kind=body.get("kind", "depends_on"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ebc_maturity_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        key = body.get("capability_key") or request.rel_url.query.get("capability_key") or None
        return json_response(_suite().maturity.assess(capability_key=key or None), status=201 if request.method == "POST" else 200)
    except Exception as exc:
        return _handle_error(exc)


async def ebc_impact_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().impact.analyze(
                capability_key=body.get("capability_key", ""),
                change=body.get("change", "process_change"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ebc_advise_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        return json_response(_suite().engine.advise(limit=int(body.get("limit", 5) or 5)), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ebc_roadmap_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        return json_response(
            _suite().roadmap.generate(horizon_quarters=int(body.get("horizon_quarters", 8) or 8)),
            status=201 if request.method == "POST" else 200,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ebc_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard.render())
    except Exception as exc:
        return _handle_error(exc)


async def ebc_analytics_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        return json_response(
            {
                "maturity": suite.maturity_analytics.report(),
                "dependencies": suite.dependency_analytics.report(),
                "performance": suite.performance.report(),
                "strategy": suite.strategy_analytics.report(),
            }
        )
    except Exception as exc:
        return _handle_error(exc)
