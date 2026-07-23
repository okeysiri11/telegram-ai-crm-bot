"""API handlers — Enterprise Knowledge Platform (Sprint 20.3)."""

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
    return enterprise_hub.knowledge_platform


async def ekp_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "enterprise_knowledge_ready": health.get("enterprise_knowledge_ready"),
            "rag_ready": health.get("rag_ready"),
            "knowledge_graph_ready": health.get("knowledge_graph_ready"),
            "vector_index_ready": health.get("vector_index_ready"),
            "suite": _suite().status(),
        }
    )


async def ekp_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ekp_documents_handler(request: web.Request) -> web.Response:
    try:
        docs = _suite().documents
        if request.method == "GET":
            return json_response(docs.status())
        body = await _read_json(request)
        return json_response(
            docs.ingest(
                title=body.get("title", ""),
                content=body.get("content", ""),
                doc_type=body.get("doc_type", "markdown"),
                owner=body.get("owner", "platform"),
                tags=body.get("tags") if isinstance(body.get("tags"), list) else None,
                department=body.get("department"),
                classification=body.get("classification", "internal"),
                version=body.get("version", "1.0"),
                source=body.get("source"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ekp_index_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().index_document(document_id=body.get("document_id", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ekp_rag_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().rag.answer(
                query=body.get("query", ""),
                mode=body.get("mode", "hybrid"),
                top_k=int(body.get("top_k", 5) or 5),
                expand=bool(body.get("expand", True)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ekp_search_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            query = request.rel_url.query.get("q", "")
            mode = request.rel_url.query.get("mode", "semantic")
            return json_response(_suite().semantic.search(query=query, mode=mode))
        body = await _read_json(request)
        return json_response(
            _suite().retrieval.retrieve(
                query=body.get("query", ""),
                mode=body.get("mode", "hybrid"),
                top_k=int(body.get("top_k", 5) or 5),
                expand=bool(body.get("expand", False)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ekp_graph_handler(request: web.Request) -> web.Response:
    try:
        graph = _suite().graph
        if request.method == "GET":
            entity_id = request.rel_url.query.get("entity_id")
            if entity_id:
                return json_response(graph.neighbors(entity_id=entity_id))
            return json_response(graph.status())
        body = await _read_json(request)
        action = (body.get("action") or "entity").lower()
        if action == "link":
            return json_response(
                graph.link(
                    source_id=body.get("source_id", ""),
                    target_id=body.get("target_id", ""),
                    relation=body.get("relation", "related_to"),
                ),
                status=201,
            )
        return json_response(
            graph.add_entity(
                kind=body.get("kind", "document"),
                name=body.get("name", ""),
                meta=body.get("meta") if isinstance(body.get("meta"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ekp_memory_handler(request: web.Request) -> web.Response:
    try:
        mem = _suite().memory
        if request.method == "GET":
            return json_response(
                {
                    "status": mem.status(),
                    "items": mem.recall(
                        tier=request.rel_url.query.get("tier"),
                        key=request.rel_url.query.get("key"),
                    ),
                }
            )
        body = await _read_json(request)
        action = (body.get("action") or "store").lower()
        if action == "context":
            return json_response(
                mem.build_context(tiers=body.get("tiers") if isinstance(body.get("tiers"), list) else None),
                status=201,
            )
        return json_response(
            mem.store_memory(
                tier=body.get("tier", "short_term"),
                key=body.get("key", ""),
                value=body.get("value"),
                owner=body.get("owner", "platform"),
                scope=body.get("scope"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ekp_analytics_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        kind = request.rel_url.query.get("kind", "usage") if request.method == "GET" else (await _read_json(request)).get("kind", "usage")
        if kind == "quality":
            return json_response(suite.quality.report())
        if kind == "relevance":
            return json_response(suite.relevance.report())
        return json_response(suite.usage.report())
    except Exception as exc:
        return _handle_error(exc)


async def ekp_governance_handler(request: web.Request) -> web.Response:
    try:
        mgr = _suite().manager
        if request.method == "GET":
            return json_response(mgr.status())
        body = await _read_json(request)
        action = (body.get("action") or "govern").lower()
        if action == "base":
            return json_response(
                mgr.create_base(
                    name=body.get("name", ""),
                    description=body.get("description", ""),
                    owner=body.get("owner", "platform"),
                ),
                status=201,
            )
        return json_response(
            mgr.govern(
                document_id=body.get("document_id", ""),
                owner=body.get("owner"),
                classification=body.get("classification"),
                expires_at=body.get("expires_at"),
                access=body.get("access") if isinstance(body.get("access"), list) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
