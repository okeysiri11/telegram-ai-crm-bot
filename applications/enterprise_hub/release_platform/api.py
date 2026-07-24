"""API handlers — Enterprise Release Platform (Sprint 21.8)."""

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
    return enterprise_hub.release_platform


async def erl_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "release_certification_ready": health.get("release_certification_ready"),
            "production_ready": health.get("production_ready"),
            "disaster_recovery_ready": health.get("disaster_recovery_ready"),
            "lts_baseline_ready": health.get("lts_baseline_ready"),
            "suite": _suite().status(),
        }
    )


async def erl_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def erl_certify_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().certify(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def erl_validate_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().validate_production(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def erl_migrate_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().migrate(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def erl_dr_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().disaster_recovery(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def erl_notes_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().release_notes())
    except Exception as exc:
        return _handle_error(exc)


async def erl_approve_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().approve(
                architecture=bool(body.get("architecture", True)),
                quality=bool(body.get("quality", True)),
                security=bool(body.get("security", True)),
                documentation=bool(body.get("documentation", True)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def erl_manifest_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().production_manifest())
    except Exception as exc:
        return _handle_error(exc)
