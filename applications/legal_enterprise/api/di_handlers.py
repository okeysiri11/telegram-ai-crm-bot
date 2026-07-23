"""API handlers — Document Intelligence (Sprint 17.4)."""

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
    return legal_enterprise.document_intelligence


async def di_health_handler(request: web.Request) -> web.Response:
    health = legal_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "contract_builder_ready": health.get("contract_builder_ready"),
            "document_intelligence_ready": health.get("document_intelligence_ready"),
            "ai_risk_review_ready": health.get("ai_risk_review_ready"),
            "legal_drafting_ready": health.get("legal_drafting_ready"),
            "suite": _suite().status(),
        }
    )


async def di_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def di_contracts_handler(request: web.Request) -> web.Response:
    try:
        contracts = _suite().contracts
        if request.method == "GET":
            return json_response(contracts.status())
        body = await _read_json(request)
        action = body.get("action", "generate")
        if action == "template":
            clauses = body.get("clauses") if isinstance(body.get("clauses"), list) else None
            return json_response(
                contracts.register_template(
                    name=body.get("name", ""),
                    contract_type=body.get("contract_type", "custom"),
                    clauses=clauses,
                    body=body.get("body", ""),
                ),
                status=201,
            )
        if action == "clause":
            return json_response(
                contracts.add_clause(
                    title=body.get("title", ""),
                    kind=body.get("kind", "general"),
                    text=body.get("text", ""),
                    mandatory=bool(body.get("mandatory", False)),
                ),
                status=201,
            )
        parties = body.get("parties") if isinstance(body.get("parties"), list) else None
        clause_ids = body.get("clause_ids") if isinstance(body.get("clause_ids"), list) else None
        kwargs = {
            "title": body.get("title", ""),
            "parties": parties,
            "template_id": body.get("template_id", ""),
            "clause_ids": clause_ids,
            "custom_body": body.get("custom_body", ""),
        }
        mapping = {
            "sales": contracts.generate_sales,
            "service": contracts.generate_service,
            "employment": contracts.generate_employment,
            "nda": contracts.generate_nda,
            "lease": contracts.generate_lease,
            "custom": contracts.generate_custom,
        }
        if action in mapping:
            return json_response(mapping[action](**kwargs), status=201)
        return json_response(
            contracts.generate(contract_type=body.get("contract_type", "custom"), **kwargs),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def di_ingest_handler(request: web.Request) -> web.Response:
    try:
        ingest = _suite().ingest
        if request.method == "GET":
            return json_response(ingest.status())
        body = await _read_json(request)
        action = body.get("action", "import")
        if action == "pdf":
            return json_response(
                ingest.process_pdf(
                    document_id=body.get("document_id", ""),
                    title=body.get("title", ""),
                    content=body.get("content", ""),
                ),
                status=201,
            )
        if action == "docx":
            return json_response(
                ingest.process_docx(
                    document_id=body.get("document_id", ""),
                    title=body.get("title", ""),
                    content=body.get("content", ""),
                ),
                status=201,
            )
        if action == "ocr":
            return json_response(
                ingest.run_ocr(
                    document_id=body.get("document_id", ""),
                    engine=body.get("engine", "tesseract"),
                ),
                status=201,
            )
        if action == "parse":
            return json_response(ingest.parse(document_id=body.get("document_id", "")), status=201)
        if action == "metadata":
            return json_response(
                ingest.extract_metadata(document_id=body.get("document_id", "")),
                status=201,
            )
        if action == "classify":
            return json_response(
                ingest.classify(
                    document_id=body.get("document_id", ""),
                    label=body.get("label", "other"),
                    confidence=float(body.get("confidence", 0.85) or 0.85),
                ),
                status=201,
            )
        return json_response(
            ingest.import_document(
                title=body.get("title", ""),
                format=body.get("format", "pdf"),
                uri=body.get("uri", ""),
                content=body.get("content", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def di_clauses_handler(request: web.Request) -> web.Response:
    try:
        clauses = _suite().clauses
        if request.method == "GET":
            return json_response(clauses.status())
        body = await _read_json(request)
        action = body.get("action", "detect")
        if action == "classify":
            return json_response(
                clauses.classify_clause(
                    clause_text=body.get("clause_text", ""),
                    kind=body.get("kind", "general"),
                ),
                status=201,
            )
        if action == "validate":
            return json_response(
                clauses.validate_mandatory(contract_id=body.get("contract_id", "")),
                status=201,
            )
        if action == "missing":
            return json_response(
                clauses.detect_missing(contract_id=body.get("contract_id", "")),
                status=201,
            )
        if action == "duplicates":
            return json_response(
                clauses.detect_duplicates(contract_id=body.get("contract_id", "")),
                status=201,
            )
        if action == "compare":
            return json_response(
                clauses.compare_clauses(
                    clause_a=body.get("clause_a", ""),
                    clause_b=body.get("clause_b", ""),
                ),
                status=201,
            )
        return json_response(
            clauses.detect(
                document_id=body.get("document_id", ""),
                contract_id=body.get("contract_id", ""),
                text=body.get("text", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def di_risk_handler(request: web.Request) -> web.Response:
    try:
        risk = _suite().risk
        if request.method == "GET":
            return json_response(risk.status())
        body = await _read_json(request)
        action = body.get("action", "detect")
        kwargs = {
            "contract_id": body.get("contract_id", ""),
            "document_id": body.get("document_id", ""),
        }
        mapping = {
            "detect": risk.detect_risks,
            "ambiguous": risk.detect_ambiguous,
            "contradiction": risk.detect_contradictions,
            "unbalanced": risk.detect_unbalanced,
            "compliance": risk.compliance_review,
            "gap": risk.gap_analysis,
            "revisions": risk.recommend_revisions,
            "score": risk.risk_score,
        }
        if action not in mapping:
            return json_response({"error": f"unknown action: {action}"}, status=400)
        return json_response(mapping[action](**kwargs), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def di_comparison_handler(request: web.Request) -> web.Response:
    try:
        comparison = _suite().comparison
        if request.method == "GET":
            return json_response(comparison.status())
        body = await _read_json(request)
        action = body.get("action", "versions")
        if action == "change":
            return json_response(
                comparison.track_change(
                    document_id=body.get("document_id", ""),
                    change=body.get("change", ""),
                    author=body.get("author", ""),
                ),
                status=201,
            )
        if action == "redline":
            return json_response(
                comparison.generate_redline(
                    document_a=body.get("document_a", ""),
                    document_b=body.get("document_b", ""),
                    summary=body.get("summary", ""),
                ),
                status=201,
            )
        if action == "similarity":
            return json_response(
                comparison.similarity(
                    document_a=body.get("document_a", ""),
                    document_b=body.get("document_b", ""),
                ),
                status=201,
            )
        if action == "approval":
            return json_response(
                comparison.request_approval(
                    document_id=body.get("document_id", ""),
                    requester=body.get("requester", ""),
                    approver=body.get("approver", ""),
                ),
                status=201,
            )
        changes = body.get("changes") if isinstance(body.get("changes"), list) else None
        return json_response(
            comparison.compare_versions(
                document_a=body.get("document_a", ""),
                document_b=body.get("document_b", ""),
                changes=changes,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def di_drafting_handler(request: web.Request) -> web.Response:
    try:
        drafting = _suite().drafting
        if request.method == "GET":
            return json_response(drafting.status())
        body = await _read_json(request)
        action = body.get("action", "draft")
        prompt = body.get("prompt", "")
        if action == "suggest":
            return json_response(
                drafting.suggest_clause(prompt=prompt, kind=body.get("kind", "general")),
                status=201,
            )
        if action == "optimize":
            return json_response(drafting.optimize_language(prompt=prompt), status=201)
        if action == "plain":
            return json_response(drafting.plain_language(prompt=prompt), status=201)
        if action == "summary":
            return json_response(drafting.summarize(prompt=prompt), status=201)
        if action == "negotiate":
            return json_response(drafting.negotiate(prompt=prompt), status=201)
        return json_response(
            drafting.draft(prompt=prompt, contract_type=body.get("contract_type", "custom")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def di_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dtype = request.rel_url.query.get("type", "contract")
        if request.method == "POST":
            body = await _read_json(request)
            dtype = body.get("dashboard_type", dtype)
        return json_response(_suite().dashboard.render(dashboard_type=dtype))
    except Exception as exc:
        return _handle_error(exc)


async def di_knowledge_handler(request: web.Request) -> web.Response:
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
