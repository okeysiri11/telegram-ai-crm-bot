"""API handlers — Judicial Intelligence (Sprint 17.2)."""

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
    return legal_enterprise.judicial_intelligence


async def ji_health_handler(request: web.Request) -> web.Response:
    health = legal_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "judicial_intelligence_ready": health.get("judicial_intelligence_ready"),
            "court_decision_repository_ready": health.get("court_decision_repository_ready"),
            "ai_judicial_analysis_ready": health.get("ai_judicial_analysis_ready"),
            "case_law_intelligence_ready": health.get("case_law_intelligence_ready"),
            "suite": _suite().status(),
        }
    )


async def ji_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ji_repository_handler(request: web.Request) -> web.Response:
    try:
        repo = _suite().repository
        if request.method == "GET":
            return json_response(repo.status())
        body = await _read_json(request)
        action = body.get("action", "judgment")
        if action == "version":
            return json_response(
                repo.record_version(
                    decision_id=body.get("decision_id", ""),
                    version=body.get("version", ""),
                    summary=body.get("summary", ""),
                ),
                status=201,
            )
        participants = body.get("participants") if isinstance(body.get("participants"), list) else None
        articles = body.get("articles") if isinstance(body.get("articles"), list) else None
        metadata = body.get("metadata") if isinstance(body.get("metadata"), dict) else None
        kwargs = {
            "title": body.get("title", ""),
            "decision_number": body.get("decision_number", ""),
            "case_number": body.get("case_number", ""),
            "court_id": body.get("court_id", ""),
            "court_name": body.get("court_name", ""),
            "judge_id": body.get("judge_id", ""),
            "judge_name": body.get("judge_name", ""),
            "decided_on": body.get("decided_on", ""),
            "outcome": body.get("outcome", ""),
            "summary": body.get("summary", ""),
            "body": body.get("body", ""),
            "participants": participants,
            "articles": articles,
            "metadata": metadata,
        }
        mapping = {
            "judgment": repo.register_judgment,
            "ruling": repo.register_ruling,
            "order": repo.register_order,
            "opinion": repo.register_opinion,
        }
        if action in mapping:
            return json_response(mapping[action](**kwargs), status=201)
        return json_response(
            repo.register(decision_type=body.get("decision_type", "judgment"), **kwargs),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ji_search_handler(request: web.Request) -> web.Response:
    try:
        search = _suite().search
        if request.method == "GET":
            return json_response(search.status())
        body = await _read_json(request)
        action = body.get("action", "semantic")
        query = body.get("query", "")
        limit = int(body.get("limit", 10) or 10)
        mapping = {
            "semantic": search.semantic,
            "decision_number": search.decision_number,
            "case_number": search.case_number,
            "judge": search.judge,
            "court": search.court,
            "participant": search.participant,
            "article": search.article,
            "keyword": search.keyword,
            "similar": search.similar,
        }
        if action in mapping:
            return json_response(mapping[action](query=query, limit=limit), status=201)
        return json_response(
            search.search(mode=body.get("mode", "semantic"), query=query, limit=limit),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ji_case_law_handler(request: web.Request) -> web.Response:
    try:
        case_law = _suite().case_law
        if request.method == "GET":
            return json_response(case_law.status())
        body = await _read_json(request)
        action = body.get("action", "classify_case")
        if action == "classify_case":
            return json_response(
                case_law.classify_case(
                    decision_id=body.get("decision_id", ""),
                    label=body.get("label", ""),
                    confidence=float(body.get("confidence", 0.85) or 0.85),
                ),
                status=201,
            )
        if action == "classify_topic":
            return json_response(
                case_law.classify_topic(
                    decision_id=body.get("decision_id", ""),
                    label=body.get("label", ""),
                    confidence=float(body.get("confidence", 0.8) or 0.8),
                ),
                status=201,
            )
        if action == "relate":
            return json_response(
                case_law.relate(
                    from_decision_id=body.get("from_decision_id", ""),
                    to_decision_id=body.get("to_decision_id", ""),
                    relation=body.get("relation", "related"),
                    detail=body.get("detail", ""),
                ),
                status=201,
            )
        if action == "cite_article":
            return json_response(
                case_law.cite_article(
                    decision_id=body.get("decision_id", ""),
                    article_ref=body.get("article_ref", ""),
                    detail=body.get("detail", ""),
                ),
                status=201,
            )
        if action == "cite_decision":
            return json_response(
                case_law.cite_decision(
                    decision_id=body.get("decision_id", ""),
                    referenced_decision_id=body.get("referenced_decision_id", ""),
                    detail=body.get("detail", ""),
                ),
                status=201,
            )
        if action == "conflict":
            return json_response(
                case_law.detect_conflict(
                    decision_a=body.get("decision_a", ""),
                    decision_b=body.get("decision_b", ""),
                    severity=body.get("severity", "medium"),
                    detail=body.get("detail", ""),
                ),
                status=201,
            )
        return json_response({"error": f"unknown action: {action}"}, status=400)
    except Exception as exc:
        return _handle_error(exc)


async def ji_judges_handler(request: web.Request) -> web.Response:
    try:
        judges = _suite().judges
        if request.method == "GET":
            return json_response(judges.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "history":
            return json_response(
                judges.record_decision(
                    judge_id=body.get("judge_id", ""),
                    decision_id=body.get("decision_id", ""),
                ),
                status=201,
            )
        if action == "statistics":
            return json_response(
                judges.decision_statistics(judge_id=body.get("judge_id", "")),
                status=201,
            )
        if action == "subjects":
            return json_response(
                judges.subject_matter_analysis(judge_id=body.get("judge_id", "")),
                status=201,
            )
        if action == "workload":
            return json_response(
                judges.workload_analytics(
                    judge_id=body.get("judge_id", ""),
                    period=body.get("period", "ytd"),
                ),
                status=201,
            )
        subjects = body.get("subjects") if isinstance(body.get("subjects"), list) else None
        return json_response(
            judges.register_judge(
                full_name=body.get("full_name", ""),
                court_id=body.get("court_id", ""),
                court_name=body.get("court_name", ""),
                title=body.get("title", "Judge"),
                subjects=subjects,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ji_analysis_handler(request: web.Request) -> web.Response:
    try:
        analysis = _suite().analysis
        if request.method == "GET":
            return json_response(analysis.status())
        body = await _read_json(request)
        action = body.get("action", "summarize")
        findings = body.get("findings") if isinstance(body.get("findings"), list) else None
        kwargs = {"decision_id": body.get("decision_id", ""), "findings": findings}
        mapping = {
            "summarize": analysis.summarize,
            "reasoning": analysis.extract_reasoning,
            "legal_basis": analysis.identify_legal_basis,
            "key_arguments": analysis.extract_key_arguments,
            "outcome": analysis.classify_outcome,
            "trend": analysis.trend_analysis,
            "pattern": analysis.detect_pattern,
            "similar_case": analysis.similar_case,
        }
        if action in mapping:
            return json_response(mapping[action](**kwargs), status=201)
        return json_response(
            analysis.analyze(
                kind=body.get("kind", "summarize"),
                decision_id=kwargs["decision_id"],
                title=body.get("title", ""),
                findings=findings,
                score=float(body.get("score", 0.8) or 0.8),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ji_analytics_handler(request: web.Request) -> web.Response:
    try:
        analytics = _suite().analytics
        if request.method == "GET":
            return json_response(analytics.status())
        body = await _read_json(request)
        return json_response(
            analytics.report(kind=body.get("kind", "timeline"), scope=body.get("scope", "all")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ji_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dtype = request.rel_url.query.get("type", "court")
        if request.method == "POST":
            body = await _read_json(request)
            dtype = body.get("dashboard_type", dtype)
        return json_response(_suite().dashboard.render(dashboard_type=dtype))
    except Exception as exc:
        return _handle_error(exc)


async def ji_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                base=body.get("base", ""),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
