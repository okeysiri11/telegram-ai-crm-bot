"""API handlers — Enterprise Digital Twin 2.0 (Sprint 24.5)."""

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
    return enterprise_hub.enterprise_digital_twin


async def etw_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "enterprise_digital_twin_ready": health.get("enterprise_digital_twin_ready"),
            "live_state_ready": health.get("live_state_ready"),
            "twin_sync_ready": health.get("twin_sync_ready"),
            "twin_time_machine_ready": health.get("twin_time_machine_ready"),
            "suite": _suite().status(),
        }
    )


async def etw_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def etw_create_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().create_twin(
                company_id=body.get("company_id", ""),
                structure=body.get("structure"),
                branches=body.get("branches"),
                employees=body.get("employees"),
                customers=body.get("customers"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def etw_state_handler(request: web.Request) -> web.Response:
    try:
        company_id = request.rel_url.query.get("company_id", "")
        if request.method == "POST":
            body = await _read_json(request)
            company_id = body.get("company_id", company_id)
        return json_response(_suite().twin_state(company_id=company_id))
    except Exception as exc:
        return _handle_error(exc)


async def etw_live_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().live_state(company_id=body.get("company_id", ""), metrics=body.get("metrics")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def etw_org_handler(request: web.Request) -> web.Response:
    try:
        company_id = request.rel_url.query.get("company_id", "")
        if request.method == "POST":
            body = await _read_json(request)
            company_id = body.get("company_id", company_id)
        return json_response(_suite().organization_map(company_id=company_id))
    except Exception as exc:
        return _handle_error(exc)


async def etw_processes_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        company_id = body.get("company_id") or request.rel_url.query.get("company_id", "")
        return json_response(_suite().processes(company_id=company_id, processes=body.get("processes")))
    except Exception as exc:
        return _handle_error(exc)


async def etw_sync_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().sync_twin(company_id=body.get("company_id", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def etw_timemachine_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        company_id = body.get("company_id") or request.rel_url.query.get("company_id", "")
        preset = body.get("preset") or request.rel_url.query.get("preset", "1h")
        return json_response(
            _suite().time_machine(
                company_id=company_id,
                preset=preset,
                custom_label=body.get("custom_label", ""),
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def etw_impact_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().change_impact(
                changed_objects=body.get("changed_objects"),
                affected_processes=body.get("affected_processes"),
                ai_consumers=body.get("ai_consumers"),
                updated_forecasts=body.get("updated_forecasts"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def etw_dashboard_handler(request: web.Request) -> web.Response:
    try:
        company_id = request.rel_url.query.get("company_id", "")
        if request.method == "POST":
            body = await _read_json(request)
            company_id = body.get("company_id", company_id)
        return json_response(_suite().owner_dashboard(company_id=company_id))
    except Exception as exc:
        return _handle_error(exc)
