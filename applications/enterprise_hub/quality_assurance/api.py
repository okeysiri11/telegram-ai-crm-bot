"""API handlers — Enterprise Quality Assurance (Sprint 21.5)."""

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
    return enterprise_hub.quality_assurance


async def eqa_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "quality_assurance_ready": health.get("quality_assurance_ready"),
            "test_framework_ready": health.get("test_framework_ready"),
            "coverage_engine_ready": health.get("coverage_engine_ready"),
            "quality_certification_ready": health.get("quality_certification_ready"),
            "suite": _suite().status(),
        }
    )


async def eqa_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def eqa_suites_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            items = suite.store.eqa_suites.list_all()
            return json_response({"suites": len(items), "items": items})
        body = await _read_json(request)
        return json_response(suite.run_suite(body.get("kind", "unit")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def eqa_coverage_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().coverage(), status=201 if request.method == "POST" else 200)
    except Exception as exc:
        return _handle_error(exc)


async def eqa_fixtures_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        kind = body.get("kind") or request.rel_url.query.get("kind", "organization")
        count = int(body.get("count") or request.rel_url.query.get("count", 3) or 3)
        return json_response(_suite().fixtures(kind=kind, count=count), status=201 if request.method == "POST" else 200)
    except Exception as exc:
        return _handle_error(exc)


async def eqa_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def eqa_certify_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().certify(), status=201)
    except Exception as exc:
        return _handle_error(exc)
