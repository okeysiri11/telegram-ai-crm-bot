"""API handlers — Legislation Intelligence (Sprint 17.1)."""

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
    return legal_enterprise.legislation_intelligence


async def li_health_handler(request: web.Request) -> web.Response:
    health = legal_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "legislation_intelligence_ready": health.get("legislation_intelligence_ready"),
            "ai_legal_search_ready": health.get("ai_legal_search_ready"),
            "regulatory_intelligence_ready": health.get("regulatory_intelligence_ready"),
            "legal_knowledge_platform_ready": health.get("legal_knowledge_platform_ready"),
            "suite": _suite().status(),
        }
    )


async def li_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def li_repository_handler(request: web.Request) -> web.Response:
    try:
        repo = _suite().repository
        if request.method == "GET":
            return json_response(repo.status())
        body = await _read_json(request)
        action = body.get("action", "ingest")
        articles = body.get("articles") if isinstance(body.get("articles"), list) else None
        kwargs = {
            "title": body.get("title", ""),
            "code": body.get("code", ""),
            "jurisdiction": body.get("jurisdiction", ""),
            "authority": body.get("authority", ""),
            "effective_on": body.get("effective_on", ""),
            "body": body.get("body", ""),
            "articles": articles,
        }
        mapping = {
            "constitution": repo.ingest_constitution,
            "code": repo.ingest_code,
            "law": repo.ingest_law,
            "regulation": repo.ingest_regulation,
            "government_resolution": repo.ingest_government_resolution,
            "ministerial_order": repo.ingest_ministerial_order,
            "international_treaty": repo.ingest_treaty,
            "local_regulation": repo.ingest_local_regulation,
        }
        if action in mapping:
            return json_response(mapping[action](**kwargs), status=201)
        return json_response(
            repo.ingest(repo_type=body.get("repo_type", "law"), **kwargs),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def li_versions_handler(request: web.Request) -> web.Response:
    try:
        versions = _suite().versions
        if request.method == "GET":
            return json_response(versions.status())
        body = await _read_json(request)
        action = body.get("action", "history")
        if action == "compare":
            changes = body.get("changes") if isinstance(body.get("changes"), list) else None
            return json_response(
                versions.compare_versions(
                    document_id=body.get("document_id", ""),
                    from_version=body.get("from_version", ""),
                    to_version=body.get("to_version", ""),
                    changes=changes,
                ),
                status=201,
            )
        if action == "amendment":
            return json_response(
                versions.track_amendment(
                    document_id=body.get("document_id", ""),
                    amendment_ref=body.get("amendment_ref", ""),
                    description=body.get("description", ""),
                    effective_on=body.get("effective_on", ""),
                ),
                status=201,
            )
        if action == "repealed":
            return json_response(
                versions.mark_repealed(
                    document_id=body.get("document_id", ""),
                    repealed_on=body.get("repealed_on", ""),
                    replaced_by=body.get("replaced_by", ""),
                    reason=body.get("reason", ""),
                ),
                status=201,
            )
        if action == "effective":
            return json_response(
                versions.track_effective_date(
                    document_id=body.get("document_id", ""),
                    effective_on=body.get("effective_on", ""),
                    event=body.get("event", "enters_force"),
                ),
                status=201,
            )
        if action == "snapshot":
            payload = body.get("payload") if isinstance(body.get("payload"), dict) else None
            return json_response(
                versions.snapshot(
                    document_id=body.get("document_id", ""),
                    label=body.get("label", ""),
                    payload=payload,
                ),
                status=201,
            )
        return json_response(
            versions.record_history(
                document_id=body.get("document_id", ""),
                version=body.get("version", ""),
                summary=body.get("summary", ""),
                effective_on=body.get("effective_on", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def li_regulatory_handler(request: web.Request) -> web.Response:
    try:
        regulatory = _suite().regulatory
        if request.method == "GET":
            return json_response(regulatory.status())
        body = await _read_json(request)
        action = body.get("action", "classify")
        kwargs = {
            "document_id": body.get("document_id", ""),
            "label": body.get("label", ""),
            "confidence": float(body.get("confidence", 0.8) or 0.8),
        }
        mapping = {
            "law": regulatory.classify_law,
            "industry": regulatory.classify_industry,
            "topic": regulatory.classify_topic,
            "jurisdiction": regulatory.classify_jurisdiction,
            "authority": regulatory.classify_authority,
        }
        if action in mapping:
            return json_response(mapping[action](**kwargs), status=201)
        return json_response(
            regulatory.classify(
                document_id=kwargs["document_id"],
                classifier=body.get("classifier", "law"),
                label=kwargs["label"],
                confidence=kwargs["confidence"],
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def li_search_handler(request: web.Request) -> web.Response:
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
            "natural_language": search.natural_language,
            "article": search.article,
            "keyword": search.keyword,
            "cross_reference": search.cross_reference,
            "citation": search.citation,
            "related": search.related,
        }
        if action in mapping:
            return json_response(mapping[action](query=query, limit=limit), status=201)
        filters = body.get("filters") if isinstance(body.get("filters"), dict) else None
        return json_response(
            search.search(mode=body.get("mode", "semantic"), query=query, limit=limit, filters=filters),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def li_cross_refs_handler(request: web.Request) -> web.Response:
    try:
        xref = _suite().cross_refs
        if request.method == "GET":
            return json_response(xref.status())
        body = await _read_json(request)
        action = body.get("action", "link")
        if action == "conflict":
            return json_response(
                xref.detect_conflict(
                    document_a=body.get("document_a", ""),
                    document_b=body.get("document_b", ""),
                    severity=body.get("severity", "medium"),
                    detail=body.get("detail", ""),
                ),
                status=201,
            )
        if action == "duplicate":
            return json_response(
                xref.detect_duplicate(
                    document_a=body.get("document_a", ""),
                    document_b=body.get("document_b", ""),
                    similarity=float(body.get("similarity", 0.9) or 0.9),
                    detail=body.get("detail", ""),
                ),
                status=201,
            )
        return json_response(
            xref.link(
                from_id=body.get("from_id", ""),
                to_id=body.get("to_id", ""),
                relation=body.get("relation", "referenced_law"),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def li_analysis_handler(request: web.Request) -> web.Response:
    try:
        analysis = _suite().analysis
        if request.method == "GET":
            return json_response(analysis.status())
        body = await _read_json(request)
        action = body.get("action", "summarize")
        findings = body.get("findings") if isinstance(body.get("findings"), list) else None
        kwargs = {
            "document_id": body.get("document_id", ""),
            "title": body.get("title", ""),
            "findings": findings,
        }
        mapping = {
            "summarize": analysis.summarize,
            "plain_language": analysis.plain_language,
            "conflict": analysis.identify_conflicts,
            "gap": analysis.gap_analysis,
            "legal_impact": analysis.legal_impact,
            "change_impact": analysis.change_impact,
        }
        if action in mapping:
            return json_response(mapping[action](**kwargs), status=201)
        return json_response(
            analysis.analyze(
                kind=body.get("kind", "summarize"),
                document_id=kwargs["document_id"],
                title=kwargs["title"],
                findings=findings,
                score=float(body.get("score", 0.8) or 0.8),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def li_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dtype = request.rel_url.query.get("type", "legislation")
        if request.method == "POST":
            body = await _read_json(request)
            dtype = body.get("dashboard_type", dtype)
        return json_response(_suite().dashboard.render(dashboard_type=dtype))
    except Exception as exc:
        return _handle_error(exc)


async def li_knowledge_handler(request: web.Request) -> web.Response:
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
