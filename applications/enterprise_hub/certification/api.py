"""API handlers — Certification (Sprint 25.7)."""

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
    return enterprise_hub.certification


async def ecf_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "certification_ready": health.get("certification_ready"),
            "quality_gates_ready": health.get("quality_gates_ready"),
            "release_builder_ready": health.get("release_builder_ready"),
            "enterprise_certified": health.get("enterprise_certified"),
            "enterprise_ready": health.get("enterprise_ready"),
            "suite": _suite().status(),
        }
    )


async def ecf_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ecf_gate_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().run_gate(
                release=body.get("release"),
                failed_gates=body.get("failed_gates"),
                missing_architecture=body.get("missing_architecture"),
                missing_docs=body.get("missing_docs"),
                readiness_scores=body.get("readiness_scores"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ecf_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)
