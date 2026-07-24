"""API handlers — Beauty Operating System (Sprint 22.2)."""

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
    return enterprise_hub.beauty_os


async def bos_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "beauty_os_ready": health.get("beauty_os_ready"),
            "beauty_appointments_ready": health.get("beauty_appointments_ready"),
            "beauty_dashboard_ready": health.get("beauty_dashboard_ready"),
            "beauty_integrations_ready": health.get("beauty_integrations_ready"),
            "suite": _suite().status(),
        }
    )


async def bos_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def bos_company_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        allowed = ("name", "timezone", "currency", "contacts", "social", "tax", "schedule", "logo")
        payload = {k: body[k] for k in allowed if k in body}
        if "name" not in payload:
            payload["name"] = body.get("name", "")
        return json_response(_suite().create_company(**payload), status=201)
    except TypeError as exc:
        return _handle_error(ValidationError(str(exc)))
    except Exception as exc:
        return _handle_error(exc)


async def bos_branch_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().create_branch(
                name=body.get("name", ""),
                schedule=body.get("schedule"),
                address=body.get("address", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def bos_employee_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().create_employee(
                name=body.get("name", ""),
                role=body.get("role", ""),
                specialization=body.get("specialization", ""),
                services=body.get("services"),
                commission_pct=float(body.get("commission_pct", 0.4) or 0.4),
                salary=float(body.get("salary", 0) or 0),
                schedule=body.get("schedule"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def bos_service_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().create_service(
                name=body.get("name", ""),
                category=body.get("category", ""),
                duration_min=int(body.get("duration_min", 0) or 0),
                price=float(body.get("price", 0) or 0),
                materials=body.get("materials"),
                performers=body.get("performers"),
                description=body.get("description", ""),
                photos=body.get("photos"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def bos_customer_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().create_customer(
                name=body.get("name", ""),
                preferences=body.get("preferences"),
                allergies=body.get("allergies"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def bos_appointment_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        if request.method == "POST" and body.get("status") and body.get("appointment_id"):
            return json_response(
                _suite().transition_appointment(
                    appointment_id=body["appointment_id"],
                    status=body["status"],
                )
            )
        return json_response(
            _suite().book_appointment(
                customer_id=body.get("customer_id", ""),
                service_id=body.get("service_id", ""),
                employee_id=body.get("employee_id", ""),
                branch_id=body.get("branch_id", ""),
                start=body.get("start", ""),
                end=body.get("end", ""),
                resource_id=body.get("resource_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def bos_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)
