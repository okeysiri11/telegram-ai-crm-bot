"""API handlers — AI Provider Hub (Sprint 24.9)."""

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
    return enterprise_hub.ai_provider_hub


async def aph_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "ai_provider_hub_ready": health.get("ai_provider_hub_ready"),
            "model_router_ready": health.get("model_router_ready"),
            "fallback_engine_ready": health.get("fallback_engine_ready"),
            "ai_cost_control_ready": health.get("ai_cost_control_ready"),
            "suite": _suite().status(),
        }
    )


async def aph_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def aph_provider_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().register_provider(
                provider_id=body.get("provider_id") or f"prov_{uuid.uuid4().hex[:8]}",
                name=body.get("name", ""),
                kind=body.get("kind", "openai"),
                endpoint=body.get("endpoint", ""),
                api_version=body.get("api_version", "v1"),
                supported_models=body.get("supported_models"),
                cost_per_1k=float(body.get("cost_per_1k", body.get("cost", 0))),
                limits=body.get("limits"),
                sla=body.get("sla"),
                status=body.get("status", "active"),
                priority=int(body.get("priority", 100)),
                health_score=float(body.get("health_score", 1.0)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aph_providers_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().list_providers())
    except Exception as exc:
        return _handle_error(exc)


async def aph_model_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().register_model(
                model_id=body.get("model_id") or f"mdl_{uuid.uuid4().hex[:8]}",
                provider_id=body.get("provider_id", ""),
                model_type=body.get("model_type", body.get("type", "chat")),
                context_window=int(body.get("context_window", body.get("context", 8192))),
                max_output=int(body.get("max_output", body.get("max_response_size", 2048))),
                cost_per_1k=float(body.get("cost_per_1k", body.get("cost", 0))),
                speed_score=float(body.get("speed_score", body.get("speed", 0.5))),
                quality_score=float(body.get("quality_score", body.get("quality_rating", 0.5))),
                capabilities=body.get("capabilities"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aph_models_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().list_models())
    except Exception as exc:
        return _handle_error(exc)


async def aph_route_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().route(
                task_type=body.get("task_type", "general_chat"),
                prefer_cost=bool(body.get("prefer_cost", False)),
                prefer_speed=bool(body.get("prefer_speed", False)),
                prefer_quality=bool(body.get("prefer_quality", True)),
                require_local=bool(body.get("require_local", False)),
                security_tier=body.get("security_tier", "standard"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aph_fallback_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().fallback(chain=body.get("chain"), fail_until=int(body.get("fail_until", 0))),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aph_prompt_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().assemble_prompt(
                template=body.get("template", ""),
                system_instructions=body.get("system_instructions", ""),
                brand_dna=body.get("brand_dna"),
                enterprise_context=body.get("enterprise_context"),
                knowledge_graph_refs=body.get("knowledge_graph_refs"),
                security_policy=body.get("security_policy"),
                user_prompt=body.get("user_prompt", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aph_cost_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().track_cost(entries=body.get("entries")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def aph_analytics_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().usage_analytics(requests=body.get("requests")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def aph_security_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().secure(
                secret_ref=body.get("secret_ref", ""),
                allowed_models=body.get("allowed_models"),
                actor=body.get("actor", "system"),
                action=body.get("action", "invoke"),
                corporate_rules=body.get("corporate_rules"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aph_invoke_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().invoke(
                task_type=body.get("task_type", "general_chat"),
                user_prompt=body.get("user_prompt", ""),
                prefer_quality=bool(body.get("prefer_quality", True)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
