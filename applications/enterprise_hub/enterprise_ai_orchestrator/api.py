"""API handlers — Enterprise AI Orchestrator (Sprint 24.0 / v7.0)."""

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
    return enterprise_hub.enterprise_ai_orchestrator


async def eao_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "enterprise_ai_orchestrator_ready": health.get("enterprise_ai_orchestrator_ready"),
            "multi_agent_council_ready": health.get("multi_agent_council_ready"),
            "council_decision_ready": health.get("council_decision_ready"),
            "owner_decision_center_ready": health.get("owner_decision_center_ready"),
            "platform_version": health["application_version"],
            "suite": _suite().status(),
        }
    )


async def eao_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def eao_agents_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response(_suite().list_agents())
        body = await _read_json(request)
        return json_response(
            _suite().register_agent(
                agent_id=body.get("agent_id", ""),
                role=body.get("role", ""),
                competencies=body.get("competencies"),
                access_level=body.get("access_level", "council"),
                status=body.get("status", "active"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eao_convene_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().convene(
                problem=body.get("problem", ""),
                required_roles=body.get("required_roles"),
                context=body.get("context"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eao_learn_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().learn(
                forecast=body.get("forecast", ""),
                actual=body.get("actual", ""),
                confirmed=bool(body.get("confirmed", False)),
                recommendation_adjustment=body.get("recommendation_adjustment", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eao_owner_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().owner_decide(
                action=body.get("action", ""),
                actor=body.get("actor", ""),
                decision_id=body.get("decision_id", ""),
                changes=body.get("changes", ""),
                notes=body.get("notes", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
