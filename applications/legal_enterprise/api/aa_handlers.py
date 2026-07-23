"""API handlers — AI Legal Assistant (Sprint 17.6)."""

from __future__ import annotations

from aiohttp import web

from applications.legal_enterprise import legal_enterprise
from applications.legal_enterprise.api.middleware import json_response
from applications.legal_enterprise.shared.exceptions import NotFoundError, ValidationError


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
    return legal_enterprise.ai_legal_assistant


async def aa_health_handler(request: web.Request) -> web.Response:
    health = legal_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "ai_legal_assistant_ready": health.get("ai_legal_assistant_ready"),
            "legal_research_engine_ready": health.get("legal_research_engine_ready"),
            "legal_reasoning_ready": health.get("legal_reasoning_ready"),
            "ai_legal_intelligence_ready": health.get("ai_legal_intelligence_ready"),
            "suite": _suite().status(),
        }
    )


async def aa_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def aa_assistant_handler(request: web.Request) -> web.Response:
    try:
        asst = _suite().assistant
        if request.method == "GET":
            return json_response(asst.status())
        body = await _read_json(request)
        action = body.get("action", "ask")
        if action == "workspace":
            return json_response(
                asst.create_workspace(name=body.get("name", ""), owner=body.get("owner", "")),
                status=201,
            )
        if action == "conversation":
            return json_response(
                asst.start_conversation(
                    workspace_id=body.get("workspace_id", ""),
                    title=body.get("title", "Legal consultation"),
                ),
                status=201,
            )
        if action == "chat":
            return json_response(
                asst.chat(
                    conversation_id=body.get("conversation_id", ""),
                    message=body.get("message", ""),
                    role=body.get("role", "user"),
                ),
                status=201,
            )
        if action == "remember":
            return json_response(
                asst.remember(
                    conversation_id=body.get("conversation_id", ""),
                    key=body.get("key", ""),
                    value=body.get("value"),
                ),
                status=201,
            )
        return json_response(
            asst.ask(
                question=body.get("question", ""),
                conversation_id=body.get("conversation_id", ""),
                context=body.get("context") if isinstance(body.get("context"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aa_research_handler(request: web.Request) -> web.Response:
    try:
        research = _suite().research
        if request.method == "GET":
            return json_response(research.status())
        body = await _read_json(request)
        action = body.get("action", "semantic")
        if action == "cite":
            return json_response(
                research.cite(
                    authority=body.get("authority", ""),
                    citation_type=body.get("citation_type", "statute"),
                    detail=body.get("detail", ""),
                ),
                status=201,
            )
        if action == "related":
            return json_response(
                research.related_authorities(authority=body.get("authority", "")),
                status=201,
            )
        mode = body.get("mode") or action
        return json_response(
            research.search(
                mode=mode,
                query=body.get("query", ""),
                limit=int(body.get("limit", 10) or 10),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aa_analysis_handler(request: web.Request) -> web.Response:
    try:
        analysis = _suite().analysis
        if request.method == "GET":
            return json_response(analysis.status())
        body = await _read_json(request)
        action = body.get("action", "reason")
        query = body.get("query", "")
        if action == "issue":
            return json_response(analysis.identify_issues(query=query), status=201)
        if action == "applicable_law":
            return json_response(analysis.applicable_law(query=query), status=201)
        if action == "article":
            return json_response(analysis.extract_articles(query=query), status=201)
        if action == "case_correlation":
            return json_response(analysis.correlate_case_law(query=query), status=201)
        if action == "conflict":
            return json_response(analysis.detect_conflicts(query=query), status=201)
        if action == "argument_map":
            return json_response(analysis.map_arguments(query=query), status=201)
        if action == "analyze":
            return json_response(
                analysis.analyze(
                    kind=body.get("kind", "reasoning"),
                    query=query,
                    findings=body.get("findings") if isinstance(body.get("findings"), list) else None,
                    score=float(body.get("score", 0.8) or 0.8),
                ),
                status=201,
            )
        return json_response(analysis.reason(query=query), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def aa_opinion_handler(request: web.Request) -> web.Response:
    try:
        opinions = _suite().opinions
        if request.method == "GET":
            return json_response(opinions.status())
        body = await _read_json(request)
        return json_response(
            opinions.draft_opinion(
                issue=body.get("issue", ""),
                conclusion=body.get("conclusion", ""),
                authorities=body.get("authorities") if isinstance(body.get("authorities"), list) else None,
                risks=body.get("risks") if isinstance(body.get("risks"), list) else None,
                alternatives=body.get("alternatives") if isinstance(body.get("alternatives"), list) else None,
                counterarguments=body.get("counterarguments")
                if isinstance(body.get("counterarguments"), list)
                else None,
                notes=body.get("notes", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aa_documents_handler(request: web.Request) -> web.Response:
    try:
        docs = _suite().documents
        if request.method == "GET":
            return json_response(docs.status())
        body = await _read_json(request)
        return json_response(
            docs.analyze_document(
                action=body.get("action", "contract_analysis"),
                document_ref=body.get("document_ref", ""),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aa_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        action = body.get("action", "publish")
        if action == "navigate":
            return json_response(
                knowledge.navigate(
                    from_node=body.get("from_node", ""),
                    relation=body.get("relation", "related_to"),
                ),
                status=201,
            )
        if action == "concept":
            return json_response(
                knowledge.map_concept(
                    concept=body.get("concept", ""),
                    related=body.get("related") if isinstance(body.get("related"), list) else None,
                ),
                status=201,
            )
        if action == "relationship":
            return json_response(
                knowledge.discover_relationship(
                    from_entity=body.get("from_entity", ""),
                    to_entity=body.get("to_entity", ""),
                    relation=body.get("relation", "cites"),
                ),
                status=201,
            )
        if action == "terminology":
            return json_response(
                knowledge.terminology(term=body.get("term", ""), definition=body.get("definition", "")),
                status=201,
            )
        if action == "resolve":
            return json_response(
                knowledge.resolve_entity(
                    name=body.get("name", ""),
                    entity_type=body.get("entity_type", "authority"),
                ),
                status=201,
            )
        return json_response(
            knowledge.publish(
                base=body.get("base", "assistant"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aa_explain_handler(request: web.Request) -> web.Response:
    try:
        explain = _suite().explainability
        if request.method == "GET":
            return json_response(explain.status())
        body = await _read_json(request)
        return json_response(
            explain.explain(
                subject=body.get("subject", ""),
                reasoning_steps=body.get("reasoning_steps")
                if isinstance(body.get("reasoning_steps"), list)
                else None,
                evidence=body.get("evidence") if isinstance(body.get("evidence"), list) else None,
                legal_basis=body.get("legal_basis") if isinstance(body.get("legal_basis"), list) else None,
                citations=body.get("citations") if isinstance(body.get("citations"), list) else None,
                confidence=float(body.get("confidence", 0.82) or 0.82),
                sources=body.get("sources") if isinstance(body.get("sources"), list) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aa_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dashboard = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("dashboard_type", "assistant")
            return json_response(dashboard.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dashboard.render(dashboard_type=body.get("dashboard_type", "assistant")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
