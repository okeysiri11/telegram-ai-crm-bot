"""API handlers — Agro Enterprise Certification (Sprint 14.8)."""

from __future__ import annotations

from aiohttp import web

from applications.agro_enterprise import agro_enterprise
from applications.agro_enterprise.api.middleware import json_response
from applications.agro_enterprise.shared.exceptions import NotFoundError, ValidationError


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
    return agro_enterprise.enterprise_certification


async def aec_health_handler(request: web.Request) -> web.Response:
    health = agro_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "release_status": health.get("release_status"),
            "architecture_certified": health.get("architecture_certified"),
            "integration_certified": health.get("integration_certified"),
            "performance_certified": health.get("performance_certified"),
            "security_certified": health.get("security_certified"),
            "documentation_certified": health.get("documentation_certified"),
            "agro_enterprise_ready": health.get("agro_enterprise_ready"),
            "production_ready": health.get("production_ready"),
            "enterprise_release_ready": health.get("enterprise_release_ready"),
            "agro_enterprise_suite_released": health.get("agro_enterprise_suite_released"),
            "all_enterprise_tests_passed": health.get("all_enterprise_tests_passed"),
            "suite": _suite().status(),
        }
    )


async def aec_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def aec_architecture_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().architecture.validate())
    except Exception as exc:
        return _handle_error(exc)


async def aec_integration_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().integration.certify())
    except Exception as exc:
        return _handle_error(exc)


async def aec_performance_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().performance.benchmark())
    except Exception as exc:
        return _handle_error(exc)


async def aec_security_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().security.audit())
    except Exception as exc:
        return _handle_error(exc)


async def aec_documentation_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().documentation.certify())
    except Exception as exc:
        return _handle_error(exc)


async def aec_quality_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().quality.certify())
    except Exception as exc:
        return _handle_error(exc)


async def aec_release_handler(request: web.Request) -> web.Response:
    try:
        kind = request.rel_url.query.get("kind", "package")
        release = _suite().release
        if kind == "registry":
            return json_response(release.module_registry())
        if kind == "version":
            return json_response(release.version_manifest())
        if kind == "deployment":
            return json_response(release.deployment_manifest())
        return json_response(release.package())
    except Exception as exc:
        return _handle_error(exc)


async def aec_executive_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().status())
    except Exception as exc:
        return _handle_error(exc)


async def aec_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dtype = request.rel_url.query.get("type", "enterprise_readiness")
        if request.method == "POST":
            body = await _read_json(request)
            dtype = body.get("dashboard_type", dtype)
        return json_response(_suite().dashboard(dashboard_type=dtype))
    except Exception as exc:
        return _handle_error(exc)
