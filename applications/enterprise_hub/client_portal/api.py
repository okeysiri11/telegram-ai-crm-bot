"""API handlers — Client Portal (Sprint 22.8)."""

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
    return enterprise_hub.client_portal


async def cpl_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "client_portal_ready": health.get("client_portal_ready"),
            "online_booking_ready": health.get("online_booking_ready"),
            "mobile_experience_ready": health.get("mobile_experience_ready"),
            "portal_security_ready": health.get("portal_security_ready"),
            "suite": _suite().status(),
        }
    )


async def cpl_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def cpl_account_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().create_account(
                customer_id=body.get("customer_id", ""),
                name=body.get("name", ""),
                phone=body.get("phone", ""),
                email=body.get("email", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cpl_book_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().online_book(
                customer_id=body.get("customer_id", ""),
                branch_id=body.get("branch_id", ""),
                service_ids=list(body.get("service_ids") or []),
                employee_id=body.get("employee_id", ""),
                start=body.get("start", ""),
                end=body.get("end", ""),
                waitlist=bool(body.get("waitlist", False)),
                auto_pick=bool(body.get("auto_pick", True)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cpl_calendar_handler(request: web.Request) -> web.Response:
    try:
        customer_id = request.rel_url.query.get("customer_id", "")
        if request.method == "POST":
            body = await _read_json(request)
            customer_id = body.get("customer_id", customer_id)
        return json_response(_suite().personal_calendar(customer_id=customer_id))
    except Exception as exc:
        return _handle_error(exc)


async def cpl_loyalty_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        customer_id = body.get("customer_id") or request.rel_url.query.get("customer_id", "")
        return json_response(_suite().loyalty_center(customer_id=customer_id))
    except Exception as exc:
        return _handle_error(exc)


async def cpl_certificates_handler(request: web.Request) -> web.Response:
    try:
        customer_id = request.rel_url.query.get("customer_id", "")
        return json_response(_suite().certificates(customer_id=customer_id))
    except Exception as exc:
        return _handle_error(exc)


async def cpl_memberships_handler(request: web.Request) -> web.Response:
    try:
        customer_id = request.rel_url.query.get("customer_id", "")
        return json_response(_suite().memberships(customer_id=customer_id))
    except Exception as exc:
        return _handle_error(exc)


async def cpl_assistant_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().assistant(customer_id=body.get("customer_id", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def cpl_notifications_handler(request: web.Request) -> web.Response:
    try:
        customer_id = request.rel_url.query.get("customer_id", "")
        return json_response(_suite().notifications(customer_id=customer_id))
    except Exception as exc:
        return _handle_error(exc)


async def cpl_security_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().secure_account(
                customer_id=body.get("customer_id", ""),
                device_id=body.get("device_id", "web"),
                platform=body.get("platform", "pwa"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
