"""API handlers — Beauty Client Journey (Sprint 22.4)."""

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
    return enterprise_hub.beauty_client_journey


async def bcj_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "beauty_client_journey_ready": health.get("beauty_client_journey_ready"),
            "smart_booking_ready": health.get("smart_booking_ready"),
            "waitlist_ready": health.get("waitlist_ready"),
            "loyalty_triggers_ready": health.get("loyalty_triggers_ready"),
            "suite": _suite().status(),
        }
    )


async def bcj_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def bcj_availability_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().suggest_availability(
                service_ids=list(body.get("service_ids") or []),
                duration_min=int(body.get("duration_min", 60) or 60),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def bcj_book_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().smart_book(
                channel=body.get("channel", "online"),
                customer_id=body.get("customer_id", ""),
                service_ids=list(body.get("service_ids") or []),
                employee_id=body.get("employee_id", ""),
                branch_id=body.get("branch_id", ""),
                start=body.get("start", ""),
                end=body.get("end", ""),
                auto_pick=bool(body.get("auto_pick", False)),
                duration_min=int(body.get("duration_min", 60) or 60),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def bcj_journey_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().create_journey(
                customer_id=body.get("customer_id", ""),
                source=body.get("source", "organic"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def bcj_waitlist_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        if body.get("offer_slot"):
            return json_response(
                _suite().offer_waitlist_slot(
                    customer_id=body.get("customer_id", ""),
                    slot=body.get("slot") if isinstance(body.get("slot"), dict) else {},
                ),
                status=201,
            )
        return json_response(
            _suite().join_waitlist(
                customer_id=body.get("customer_id", ""),
                service_ids=list(body.get("service_ids") or []),
                preferred_windows=body.get("preferred_windows"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def bcj_loyalty_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().loyalty_scan(journey_id=body.get("journey_id", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def bcj_assistant_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().booking_assistant(
                service_ids=list(body.get("service_ids") or []),
                customer_id=body.get("customer_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
