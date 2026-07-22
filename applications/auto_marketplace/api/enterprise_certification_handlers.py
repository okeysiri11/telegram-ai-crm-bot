"""API handlers — Enterprise Certification (Sprint 13.9)."""

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.middleware import json_response
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError


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
    return auto_marketplace.enterprise_certification


async def ec_health_handler(request: web.Request) -> web.Response:
    health = auto_marketplace.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "release_status": health.get("release_status"),
            "architecture_certified": health.get("architecture_certified"),
            "security_certified": health.get("security_certified"),
            "performance_certified": health.get("performance_certified"),
            "documentation_certified": health.get("documentation_certified"),
            "enterprise_release_ready": health.get("enterprise_release_ready"),
            "automotive_enterprise_suite_released": health.get("automotive_enterprise_suite_released"),
            "suite": _suite().status(),
        }
    )


async def ec_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ec_architecture_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().architecture.validate())
    except Exception as exc:
        return _handle_error(exc)


async def ec_integration_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().integration.certify())
    except Exception as exc:
        return _handle_error(exc)


async def ec_performance_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().performance.benchmark())
    except Exception as exc:
        return _handle_error(exc)


async def ec_security_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().security.audit())
    except Exception as exc:
        return _handle_error(exc)


async def ec_documentation_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().documentation.certify())
    except Exception as exc:
        return _handle_error(exc)


async def ec_quality_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        return json_response(
            _suite().quality.certify(
                unit_ok=bool(body.get("unit_ok", True)),
                integration_ok=bool(body.get("integration_ok", True)),
                regression_ok=bool(body.get("regression_ok", True)),
                e2e_ok=bool(body.get("e2e_ok", True)),
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def ec_release_handler(request: web.Request) -> web.Response:
    try:
        kind = request.rel_url.query.get("kind", "manifest")
        if kind == "registry":
            return json_response(_suite().release.module_registry())
        return json_response(_suite().release.version_manifest())
    except Exception as exc:
        return _handle_error(exc)


async def ec_executive_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().run_all()["executive"])
    except Exception as exc:
        return _handle_error(exc)
