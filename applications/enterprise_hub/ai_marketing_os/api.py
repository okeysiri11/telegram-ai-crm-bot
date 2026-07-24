"""API handlers — AI Marketing OS Beauty Edition (Sprint 22.5)."""

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
    return enterprise_hub.ai_marketing_os


async def amo_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "ai_marketing_os_ready": health.get("ai_marketing_os_ready"),
            "brand_center_ready": health.get("brand_center_ready"),
            "campaign_manager_ready": health.get("campaign_manager_ready"),
            "marketing_approval_ready": health.get("marketing_approval_ready"),
            "suite": _suite().status(),
        }
    )


async def amo_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def amo_brand_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        allowed = (
            "name", "colors", "fonts", "tone_of_voice", "style", "positioning",
            "audience", "advantages", "forbidden_words", "templates", "logo",
        )
        payload = {k: body[k] for k in allowed if k in body}
        return json_response(_suite().upsert_brand(**payload), status=201)
    except TypeError as exc:
        return _handle_error(ValidationError(str(exc)))
    except Exception as exc:
        return _handle_error(exc)


async def amo_creative_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().generate_creative(
                kind=body.get("kind", ""),
                prompt=body.get("prompt", ""),
                brand_id=body.get("brand_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def amo_content_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().generate_content(
                kind=body.get("kind", ""),
                topic=body.get("topic", ""),
                brand_id=body.get("brand_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def amo_opportunities_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().detect_opportunities(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def amo_campaign_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().create_campaign(
                kind=body.get("kind", ""),
                title=body.get("title", ""),
                budget=float(body.get("budget", 0) or 0),
                channels=body.get("channels"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def amo_approve_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        if body.get("approval_id"):
            return json_response(
                _suite().owner_decide(
                    approval_id=body.get("approval_id", ""),
                    action=body.get("action", ""),
                    owner_id=body.get("owner_id", ""),
                    edits=body.get("edits") if isinstance(body.get("edits"), dict) else None,
                ),
                status=201,
            )
        return json_response(
            _suite().submit_for_approval(
                campaign_id=body.get("campaign_id", ""),
                reason=body.get("reason", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def amo_performance_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().analyze_performance(
                campaign_id=body.get("campaign_id", ""),
                observed=body.get("observed") if isinstance(body.get("observed"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
