"""API handlers — Unified Knowledge Graph & AI Memory (Sprint 19.2)."""

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
    return enterprise_hub.unified_knowledge


async def kg_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "unified_knowledge_graph_ready": health.get("unified_knowledge_graph_ready"),
            "ai_memory_ready": health.get("ai_memory_ready"),
            "semantic_intelligence_ready": health.get("semantic_intelligence_ready"),
            "cross_platform_context_ready": health.get("cross_platform_context_ready"),
            "suite": _suite().status(),
        }
    )


async def kg_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def kg_graph_handler(request: web.Request) -> web.Response:
    try:
        graph = _suite().graph
        if request.method == "GET":
            return json_response(graph.status())
        body = await _read_json(request)
        action = body.get("action", "entity")
        if action == "relate":
            return json_response(
                graph.relate(
                    from_entity_id=body.get("from_entity_id", ""),
                    to_entity_id=body.get("to_entity_id", ""),
                    relation=body.get("relation", ""),
                    weight=float(body.get("weight", 1) or 1),
                ),
                status=201,
            )
        if action == "build":
            return json_response(graph.build_graph(label=body.get("label", "enterprise")), status=201)
        if action == "link":
            return json_response(
                graph.link_cross_platform(
                    entity_id=body.get("entity_id", ""),
                    platform=body.get("platform", ""),
                    external_id=body.get("external_id", ""),
                ),
                status=201,
            )
        if action == "ontology":
            return json_response(
                graph.register_ontology(
                    name=body.get("name", ""),
                    concepts=body.get("concepts") if isinstance(body.get("concepts"), list) else None,
                    version=body.get("version", "1.0"),
                ),
                status=201,
            )
        if action == "version":
            return json_response(
                graph.version_graph(graph_id=body.get("graph_id", ""), note=body.get("note", "")),
                status=201,
            )
        return json_response(
            graph.register_entity(
                name=body.get("name", ""),
                entity_type=body.get("entity_type", "organization"),
                platform=body.get("platform", ""),
                attributes=body.get("attributes") if isinstance(body.get("attributes"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def kg_memory_handler(request: web.Request) -> web.Response:
    try:
        memory = _suite().memory
        if request.method == "GET":
            return json_response(memory.status())
        body = await _read_json(request)
        return json_response(
            memory.remember(
                memory_type=body.get("memory_type", "long_term"),
                subject=body.get("subject", ""),
                content=body.get("content", ""),
                version=int(body.get("version", 1) or 1),
                tags=body.get("tags") if isinstance(body.get("tags"), list) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def kg_semantic_handler(request: web.Request) -> web.Response:
    try:
        semantic = _suite().semantic
        if request.method == "GET":
            return json_response(semantic.status())
        body = await _read_json(request)
        return json_response(
            semantic.operate(
                operation=body.get("operation", "semantic_search"),
                query=body.get("query", ""),
                score=float(body.get("score", 0.8) or 0.8),
                results=body.get("results") if isinstance(body.get("results"), list) else None,
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def kg_context_handler(request: web.Request) -> web.Response:
    try:
        context = _suite().context
        if request.method == "GET":
            return json_response(context.status())
        body = await _read_json(request)
        return json_response(
            context.attach(
                context_type=body.get("context_type", "unified"),
                subject=body.get("subject", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def kg_ai_handler(request: web.Request) -> web.Response:
    try:
        ai = _suite().ai
        if request.method == "GET":
            return json_response(ai.status())
        body = await _read_json(request)
        action = body.get("action", "insight")
        if action == "nl_query":
            return json_response(
                ai.nl_query(question=body.get("question", ""), audience=body.get("audience", "executive")),
                status=201,
            )
        return json_response(
            ai.insight(
                insight_type=body.get("insight_type", "recommendation"),
                subject=body.get("subject", ""),
                score=float(body.get("score", 0.8) or 0.8),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def kg_sync_handler(request: web.Request) -> web.Response:
    try:
        sync = _suite().sync
        if request.method == "GET":
            return json_response(sync.status())
        body = await _read_json(request)
        action = body.get("action", "sync")
        if action == "conflict":
            return json_response(
                sync.conflict(
                    entity_ref=body.get("entity_ref", ""),
                    detail=body.get("detail", ""),
                    resolved=bool(body.get("resolved", False)),
                ),
                status=201,
            )
        if action == "resolve":
            return json_response(
                sync.resolve(
                    conflict_id=body.get("conflict_id", ""),
                    resolution=body.get("resolution", "keep_latest"),
                ),
                status=201,
            )
        if action == "audit":
            return json_response(
                sync.audit(
                    action=body.get("audit_action", "change"),
                    actor=body.get("actor", "system"),
                    detail=body.get("detail", ""),
                ),
                status=201,
            )
        if action == "monitor":
            return json_response(sync.monitor(), status=201)
        return json_response(
            sync.sync(
                platform=body.get("platform", ""),
                mode=body.get("mode", "incremental"),
                changes=int(body.get("changes", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def kg_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dashboard = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("dashboard_type", "knowledge")
            return json_response(dashboard.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dashboard.render(dashboard_type=body.get("dashboard_type", "knowledge")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def kg_meta_handler(request: web.Request) -> web.Response:
    try:
        meta = _suite().meta
        if request.method == "GET":
            return json_response(meta.status())
        body = await _read_json(request)
        return json_response(
            meta.publish(
                base=body.get("base", "master"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
