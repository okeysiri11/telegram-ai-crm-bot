"""API handlers — Simulation Lab (Sprint 24.4)."""

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
    return enterprise_hub.simulation_lab


async def esl_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "simulation_lab_ready": health.get("simulation_lab_ready"),
            "what_if_ready": health.get("what_if_ready"),
            "multi_scenario_ready": health.get("multi_scenario_ready"),
            "owner_simulation_ready": health.get("owner_simulation_ready"),
            "suite": _suite().status(),
        }
    )


async def esl_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def esl_scenario_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().create_scenario(
                scenario_id=body.get("scenario_id") or f"scn_{body.get('name', 'new').replace(' ', '_').lower()}",
                name=body.get("name", ""),
                description=body.get("description", ""),
                author=body.get("author", "platform_owner"),
                models=body.get("models"),
                status=body.get("status", "draft"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def esl_what_if_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().what_if(question=body.get("question", ""), intensity=float(body.get("intensity", 1.0))),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def esl_simulate_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().simulate(
                scenario_id=body.get("scenario_id", ""),
                question=body.get("question"),
                intensity=float(body.get("intensity", 1.0)),
                baselines=body.get("baselines"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def esl_compare_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().compare(options=list(body.get("options") or [])), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def esl_owner_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().owner_decide(
                action=body.get("action", ""),
                actor=body.get("actor", ""),
                scenario_id=body.get("scenario_id", ""),
                notes=body.get("notes", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
