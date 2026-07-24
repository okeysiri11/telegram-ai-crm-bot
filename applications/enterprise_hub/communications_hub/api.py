"""API handlers — Enterprise Communications Hub (Sprint 22.6)."""

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
    return enterprise_hub.communications_hub


async def ech_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "communications_hub_ready": health.get("communications_hub_ready"),
            "unified_messaging_ready": health.get("unified_messaging_ready"),
            "comms_automation_ready": health.get("comms_automation_ready"),
            "comms_analytics_ready": health.get("comms_analytics_ready"),
            "suite": _suite().status(),
        }
    )


async def ech_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ech_send_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        payload = {
            "channel": body.get("channel", ""),
            "recipient": body.get("recipient", ""),
            "body": body.get("body", ""),
            "template_id": body.get("template_id", ""),
            "industry": body.get("industry", "beauty"),
            "approved": bool(body.get("approved", False)),
            "automation_id": body.get("automation_id", ""),
        }
        if body.get("customer_id"):
            payload["customer_id"] = body["customer_id"]
        return json_response(_suite().send_message(**payload), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ech_template_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().create_template(
                name=body.get("name", ""),
                category=body.get("category", "general"),
                body=body.get("body", ""),
                locale=body.get("locale", "en"),
                variables=body.get("variables"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ech_automation_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().create_automation(
                scenario=body.get("scenario", ""),
                channel=body.get("channel", "sms"),
                template_name=body.get("template_name", ""),
                pre_approved=bool(body.get("pre_approved", True)),
                industry=body.get("industry", "beauty"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ech_timeline_handler(request: web.Request) -> web.Response:
    try:
        customer_id = request.rel_url.query.get("customer_id", "")
        if request.method == "POST":
            body = await _read_json(request)
            customer_id = body.get("customer_id", customer_id)
        return json_response(_suite().timeline(customer_id=customer_id))
    except Exception as exc:
        return _handle_error(exc)


async def ech_assistant_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().assistant(
                purpose=body.get("purpose", "general"),
                customer_id=body.get("customer_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ech_delivery_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().enqueue_campaign(
                campaign_id=body.get("campaign_id", ""),
                recipients=list(body.get("recipients") or []),
                channel=body.get("channel", "email"),
                body=body.get("body", ""),
                rate_limit_per_min=int(body.get("rate_limit_per_min", 120) or 120),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ech_analytics_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().analytics(
                delivered=int(body.get("delivered", 0) or 0),
                opened=int(body.get("opened", 0) or 0),
                clicks=int(body.get("clicks", 0) or 0),
                conversions=int(body.get("conversions", 0) or 0),
                bookings=int(body.get("bookings", 0) or 0),
                sales=float(body.get("sales", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
