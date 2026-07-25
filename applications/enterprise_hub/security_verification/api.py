"""API handlers — Security Verification (Sprint 25.5)."""

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
    return enterprise_hub.security_verification


async def esv_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "security_verification_ready": health.get("security_verification_ready"),
            "vulnerability_scanner_ready": health.get("vulnerability_scanner_ready"),
            "secret_scanner_ready": health.get("secret_scanner_ready"),
            "compliance_ready": health.get("compliance_ready"),
            "suite": _suite().status(),
        }
    )


async def esv_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def esv_gate_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().run_gate(
                release=body.get("release"),
                vuln_findings=body.get("vuln_findings"),
                secret_hits=body.get("secret_hits"),
                cves=body.get("cves"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def esv_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)
