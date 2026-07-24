"""API handlers — Enterprise AI Business Advisor (Sprint 22.1)."""

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
    return enterprise_hub.ai_business_advisor


async def aba_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "ai_business_advisor_ready": health.get("ai_business_advisor_ready"),
            "business_health_ready": health.get("business_health_ready"),
            "daily_brief_ready": health.get("daily_brief_ready"),
            "advisor_owner_approval_ready": health.get("advisor_owner_approval_ready"),
            "suite": _suite().status(),
        }
    )


async def aba_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def aba_analyze_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        snapshot = body.get("snapshot") if isinstance(body.get("snapshot"), dict) else None
        return json_response(
            _suite().analyze_health(industry=body.get("industry", "generic"), snapshot=snapshot),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aba_daily_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        snapshot = body.get("snapshot") if isinstance(body.get("snapshot"), dict) else None
        return json_response(
            _suite().run_daily(industry=body.get("industry", "generic"), snapshot=snapshot),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aba_brief_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().latest_brief())
    except Exception as exc:
        return _handle_error(exc)


async def aba_decide_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().owner_decide(
                recommendation_set_id=body.get("recommendation_set_id", ""),
                decision=body.get("decision", ""),
                owner_id=body.get("owner_id", ""),
                notes=body.get("notes", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
