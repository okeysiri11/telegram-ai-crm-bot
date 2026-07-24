"""API handlers — Enterprise API Standardization (Sprint 21.2)."""

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
    suite = enterprise_hub.api_standardization
    if isinstance(exc, NotFoundError):
        return json_response(
            suite.error(error_code="not_found", message=str(exc)),
            status=404,
        )
    if isinstance(exc, ValidationError):
        return json_response(
            suite.error(error_code="validation_error", message=str(exc)),
            status=400,
        )
    return json_response(
        suite.error(error_code="internal_error", message=str(exc)),
        status=500,
    )


def _suite():
    return enterprise_hub.api_standardization


async def eas_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        _suite().success(
            {
                "status": "ok",
                "application_version": health["application_version"],
                "enterprise_foundation": health.get("enterprise_foundation"),
                "api_standardization_ready": health.get("api_standardization_ready"),
                "api_inventory_ready": health.get("api_inventory_ready"),
                "openapi_ready": health.get("openapi_ready"),
                "api_governance_ready": health.get("api_governance_ready"),
                "suite": _suite().status(),
            }
        )
    )


async def eas_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def eas_inventory_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "POST":
            return json_response(suite.success(suite.inventory.scan()), status=201)
        return json_response(
            suite.success({"items": suite.inventory.list_endpoints(), **suite.inventory.status()})
        )
    except Exception as exc:
        return _handle_error(exc)


async def eas_registry_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response(suite.success({"items": suite.registry.list_all(), **suite.registry.status()}))
        body = await _read_json(request)
        created = suite.registry.register(
            path=body.get("path", ""),
            method=body.get("method", "GET"),
            category=body.get("category", "public"),
            service=body.get("service", "custom"),
            version=body.get("version", "v1"),
            deprecated=bool(body.get("deprecated", False)),
        )
        return json_response(suite.success(created), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def eas_rest_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        version = body.get("version") or request.rel_url.query.get("version", "v1")
        return json_response(_suite().success(_suite().rest.catalog(version=version)))
    except Exception as exc:
        return _handle_error(exc)


async def eas_auth_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "POST":
            body = await _read_json(request)
            headers = body.get("headers") if isinstance(body.get("headers"), dict) else {}
            return json_response(suite.success(suite.auth.validate_context(headers)))
        return json_response(suite.success(suite.auth.policy()))
    except Exception as exc:
        return _handle_error(exc)


async def eas_websocket_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().success(_suite().websocket.channels()))
    except Exception as exc:
        return _handle_error(exc)


async def eas_events_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response(suite.success(suite.events.contract()))
        body = await _read_json(request)
        if body.get("validate_only"):
            return json_response(suite.success(suite.events.validate_event(body.get("event") or body)))
        return json_response(suite.success(suite.events.publish(body.get("event") or body)), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def eas_openapi_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().success(_suite().openapi.build()))
    except Exception as exc:
        return _handle_error(exc)


async def eas_docs_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        oas = suite.openapi.build()
        return json_response(
            suite.success(
                {
                    "openapi": oas,
                    "swagger": suite.swagger.render(openapi_id=oas["openapi_id"]),
                    "redoc": suite.redoc.render(openapi_id=oas["openapi_id"]),
                }
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def eas_gateway_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().success(_suite().gateway.validate()))
    except Exception as exc:
        return _handle_error(exc)


async def eas_governance_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().success(_suite().governance.run_all()), status=201 if request.method == "POST" else 200)
    except Exception as exc:
        return _handle_error(exc)


async def eas_versioning_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        version = request.rel_url.query.get("version")
        if version:
            return json_response(suite.success(suite.versioning.resolve(version)))
        return json_response(suite.success(suite.versioning.matrix()))
    except Exception as exc:
        return _handle_error(exc)
