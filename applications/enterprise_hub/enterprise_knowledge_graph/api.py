"""API handlers — Enterprise Knowledge Graph (Sprint 24.2)."""

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
    return enterprise_hub.enterprise_knowledge_graph


async def ekg_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "knowledge_graph_ready": health.get("knowledge_graph_ready") or health.get("enterprise_knowledge_graph_ready"),
            "enterprise_knowledge_graph_ready": health.get("enterprise_knowledge_graph_ready"),
            "semantic_memory_ready": health.get("semantic_memory_ready"),
            "context_engine_ready": health.get("context_engine_ready"),
            "semantic_search_ready": health.get("semantic_search_ready"),
            "suite": _suite().status(),
        }
    )


async def ekg_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ekg_entity_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().upsert_entity(
                entity_id=body.get("entity_id", ""),
                entity_type=body.get("entity_type", ""),
                properties=body.get("properties"),
                labels=body.get("labels"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ekg_link_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().link(
                source_id=body.get("source_id", ""),
                relation=body.get("relation", ""),
                target_id=body.get("target_id", ""),
                weight=float(body.get("weight", 1.0)),
                meta=body.get("meta"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ekg_memory_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().remember(
                kind=body.get("kind", ""),
                subject_id=body.get("subject_id", ""),
                summary=body.get("summary", ""),
                payload=body.get("payload"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ekg_context_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().build_context(
                task=body.get("task", ""),
                entity_ids=body.get("entity_ids"),
                sources=body.get("sources"),
                memory=body.get("memory"),
                recommendations=body.get("recommendations"),
                outcomes=body.get("outcomes"),
                elapsed_ms=float(body.get("elapsed_ms", 2.0)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ekg_search_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        text = body.get("text") or request.rel_url.query.get("q", "")
        return json_response(_suite().semantic_search(text=text))
    except Exception as exc:
        return _handle_error(exc)


async def ekg_timeline_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        entity_id = body.get("entity_id") or request.rel_url.query.get("entity_id", "")
        return json_response(_suite().timeline(entity_id=entity_id))
    except Exception as exc:
        return _handle_error(exc)


async def ekg_learn_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().learn(
                graph_update=body.get("graph_update"),
                strengthen=body.get("strengthen"),
                archive_entity_ids=body.get("archive_entity_ids"),
                confirmed=bool(body.get("confirmed", False)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ekg_owner_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().owner_control(
                action=body.get("action", ""),
                actor=body.get("actor", ""),
                payload=body.get("payload"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
