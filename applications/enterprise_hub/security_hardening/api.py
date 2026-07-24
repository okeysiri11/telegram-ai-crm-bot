"""API handlers — Enterprise Security Hardening (Sprint 21.4)."""

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
    return enterprise_hub.security_hardening


async def esh_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "security_hardening_ready": health.get("security_hardening_ready"),
            "zero_trust_ready": health.get("zero_trust_ready"),
            "secrets_management_ready": health.get("secrets_management_ready"),
            "compliance_ready": health.get("compliance_ready"),
            "suite": _suite().status(),
        }
    )


async def esh_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def esh_authenticate_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().authenticate(
                method=body.get("method", "jwt"),
                principal=body.get("principal", ""),
                secret=body.get("secret", ""),
                mfa_code=body.get("mfa_code"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def esh_authorize_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().authorize(
                principal=body.get("principal", ""),
                roles_required=body.get("roles_required") if isinstance(body.get("roles_required"), list) else None,
                attributes=body.get("attributes") if isinstance(body.get("attributes"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def esh_zero_trust_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        return json_response(_suite().zero_trust(body.get("context") if isinstance(body.get("context"), dict) else body), status=201 if request.method == "POST" else 200)
    except Exception as exc:
        return _handle_error(exc)


async def esh_secrets_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response({"secrets": len(suite.store.esh_secrets.list_all()), "items": suite.store.esh_secrets.list_all()})
        body = await _read_json(request)
        return json_response(
            suite.put_secret(name=body.get("name", ""), kind=body.get("kind", "api_key"), value=body.get("value", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def esh_compliance_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().compliance())
    except Exception as exc:
        return _handle_error(exc)


async def esh_tests_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().run_tests(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def esh_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)
