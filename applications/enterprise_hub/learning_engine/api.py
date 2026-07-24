"""API handlers — Learning Engine (Sprint 24.8)."""

from __future__ import annotations

import uuid

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
    return enterprise_hub.learning_engine


async def ele_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "learning_engine_ready": health.get("learning_engine_ready"),
            "confirmed_learning_ready": health.get("confirmed_learning_ready"),
            "cross_tenant_learning_ready": health.get("cross_tenant_learning_ready"),
            "owner_learning_ready": health.get("owner_learning_ready"),
            "suite": _suite().status(),
        }
    )


async def ele_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ele_collect_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().collect(events=body.get("events")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ele_register_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().register(
                learning_id=body.get("learning_id") or f"lrn_{uuid.uuid4().hex[:8]}",
                source=body.get("source", ""),
                tenant=body.get("tenant", ""),
                module=body.get("module", ""),
                knowledge_type=body.get("knowledge_type", "pattern"),
                trust_level=float(body.get("trust_level", 0.5)),
                author=body.get("author", "system"),
                version=body.get("version", "1.0"),
                payload=body.get("payload"),
                confirmed=bool(body.get("confirmed", False)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ele_learnings_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().list_learnings())
    except Exception as exc:
        return _handle_error(exc)


async def ele_feedback_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().classify_feedback(text=body.get("text", "")))
    except Exception as exc:
        return _handle_error(exc)


async def ele_patterns_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().detect_patterns(items=body.get("items")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ele_cross_tenant_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().cross_tenant(anonymized_signals=body.get("signals")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ele_evolve_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().evolve(
                past_success_rate=float(body.get("past_success_rate", 0.5)),
                acceptance_rate=float(body.get("acceptance_rate", 0.5)),
                completion_rate=float(body.get("completion_rate", 0.5)),
                outcome_score=float(body.get("outcome_score", 0.5)),
                industry=body.get("industry", "general"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ele_score_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().score_agent(
                agent_id=body.get("agent_id", ""),
                accuracy=float(body.get("accuracy", 0.7)),
                usefulness=float(body.get("usefulness", 0.7)),
                accepted_advice_pct=float(body.get("accepted_advice_pct", 0.5)),
                successful_implementations_pct=float(body.get("successful_implementations_pct", 0.5)),
                user_trust=float(body.get("user_trust", 0.6)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ele_owner_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().owner_decide(
                action=body.get("action", ""),
                actor=body.get("actor", ""),
                learning_id=body.get("learning_id", ""),
                notes=body.get("notes", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ele_product_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().product_push(
                improvement=body.get("improvement", ""),
                confirmed=bool(body.get("confirmed", False)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ele_safety_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().safety_check(intent=body.get("intent", "")))
    except Exception as exc:
        return _handle_error(exc)


async def ele_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().owner_dashboard())
    except Exception as exc:
        return _handle_error(exc)
