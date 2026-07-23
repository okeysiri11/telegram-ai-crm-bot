"""API handlers — Compliance Platform (Sprint 17.5)."""

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
    return legal_enterprise.compliance_platform


async def cp_health_handler(request: web.Request) -> web.Response:
    health = legal_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "compliance_platform_ready": health.get("compliance_platform_ready"),
            "corporate_governance_ready": health.get("corporate_governance_ready"),
            "legal_risk_management_ready": health.get("legal_risk_management_ready"),
            "ai_compliance_intelligence_ready": health.get("ai_compliance_intelligence_ready"),
            "suite": _suite().status(),
        }
    )


async def cp_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def cp_governance_handler(request: web.Request) -> web.Response:
    try:
        gov = _suite().governance
        if request.method == "GET":
            return json_response(gov.status())
        body = await _read_json(request)
        action = body.get("action", "company")
        if action == "structure":
            return json_response(
                gov.register_structure(
                    company_id=body.get("company_id", ""),
                    parent_id=body.get("parent_id", ""),
                    relation=body.get("relation", "subsidiary"),
                ),
                status=201,
            )
        if action == "shareholder":
            return json_response(
                gov.register_shareholder(
                    company_id=body.get("company_id", ""),
                    name=body.get("name", ""),
                    ownership_pct=float(body.get("ownership_pct", 0) or 0),
                ),
                status=201,
            )
        if action == "board":
            return json_response(
                gov.register_board_member(
                    company_id=body.get("company_id", ""),
                    name=body.get("name", ""),
                    role=body.get("role", "director"),
                ),
                status=201,
            )
        if action == "executive":
            return json_response(
                gov.register_executive(
                    company_id=body.get("company_id", ""),
                    name=body.get("name", ""),
                    title=body.get("title", "CEO"),
                ),
                status=201,
            )
        if action == "document":
            return json_response(
                gov.register_document(
                    company_id=body.get("company_id", ""),
                    title=body.get("title", ""),
                    document_type=body.get("document_type", "charter"),
                    uri=body.get("uri", ""),
                ),
                status=201,
            )
        if action == "resolution":
            return json_response(
                gov.register_resolution(
                    company_id=body.get("company_id", ""),
                    title=body.get("title", ""),
                    adopted_on=body.get("adopted_on", ""),
                    status=body.get("status", "adopted"),
                ),
                status=201,
            )
        return json_response(
            gov.register_company(
                name=body.get("name", ""),
                jurisdiction=body.get("jurisdiction", ""),
                registration_no=body.get("registration_no", ""),
                structure=body.get("structure", "corporation"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cp_compliance_handler(request: web.Request) -> web.Response:
    try:
        cm = _suite().compliance
        if request.method == "GET":
            return json_response(cm.status())
        body = await _read_json(request)
        action = body.get("action", "framework")
        if action == "requirement":
            return json_response(
                cm.register_requirement(
                    framework_id=body.get("framework_id", ""),
                    code=body.get("code", ""),
                    title=body.get("title", ""),
                    description=body.get("description", ""),
                ),
                status=201,
            )
        if action == "checklist":
            return json_response(
                cm.checklist_item(
                    requirement_id=body.get("requirement_id", ""),
                    company_id=body.get("company_id", ""),
                    status=body.get("status", "open"),
                ),
                status=201,
            )
        if action == "status":
            return json_response(
                cm.track_status(
                    checklist_id=body.get("checklist_id", ""),
                    status=body.get("status", "compliant"),
                    note=body.get("note", ""),
                ),
                status=201,
            )
        if action == "policy":
            return json_response(
                cm.register_policy(
                    title=body.get("title", ""),
                    policy_type=body.get("policy_type", "internal"),
                    version=body.get("version", "1.0"),
                ),
                status=201,
            )
        if action == "control":
            return json_response(
                cm.register_control(
                    name=body.get("name", ""),
                    control_type=body.get("control_type", "preventive"),
                    policy_id=body.get("policy_id", ""),
                ),
                status=201,
            )
        if action == "exception":
            return json_response(
                cm.register_exception(
                    control_id=body.get("control_id", ""),
                    reason=body.get("reason", ""),
                    approved_by=body.get("approved_by", ""),
                    expires_on=body.get("expires_on", ""),
                ),
                status=201,
            )
        return json_response(
            cm.register_framework(
                name=body.get("name", ""),
                jurisdiction=body.get("jurisdiction", ""),
                version=body.get("version", "1.0"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cp_licenses_handler(request: web.Request) -> web.Response:
    try:
        licenses = _suite().licenses
        if request.method == "GET":
            return json_response(licenses.status())
        body = await _read_json(request)
        action = body.get("action", "license")
        if action == "permit":
            return json_response(
                licenses.register_permit(
                    name=body.get("name", ""),
                    issuer=body.get("issuer", ""),
                    expires_on=body.get("expires_on", ""),
                ),
                status=201,
            )
        if action == "certificate":
            return json_response(
                licenses.register_certificate(
                    name=body.get("name", ""),
                    issuer=body.get("issuer", ""),
                    expires_on=body.get("expires_on", ""),
                ),
                status=201,
            )
        if action == "monitor":
            return json_response(
                licenses.monitor_expiration(
                    license_id=body.get("license_id", ""),
                    permit_id=body.get("permit_id", ""),
                    certificate_id=body.get("certificate_id", ""),
                ),
                status=201,
            )
        if action == "renewal":
            return json_response(
                licenses.start_renewal(
                    target_id=body.get("target_id", ""),
                    kind=body.get("kind", "license"),
                    due_on=body.get("due_on", ""),
                ),
                status=201,
            )
        if action == "notify":
            return json_response(
                licenses.notify_renewal(
                    renewal_id=body.get("renewal_id", ""),
                    channel=body.get("channel", "email"),
                ),
                status=201,
            )
        return json_response(
            licenses.register_license(
                name=body.get("name", ""),
                issuer=body.get("issuer", ""),
                expires_on=body.get("expires_on", ""),
                company_id=body.get("company_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cp_counterparties_handler(request: web.Request) -> web.Response:
    try:
        ctp = _suite().counterparties
        if request.method == "GET":
            return json_response(ctp.status())
        body = await _read_json(request)
        action = body.get("action", "vendor")
        kwargs = {
            "name": body.get("name", ""),
            "country": body.get("country", ""),
            "risk_level": body.get("risk_level", "medium"),
        }
        if action == "kyc":
            return json_response(
                ctp.run_kyc(
                    counterparty_id=body.get("counterparty_id", ""),
                    status=body.get("status", "passed"),
                ),
                status=201,
            )
        if action == "kyb":
            return json_response(
                ctp.run_kyb(
                    counterparty_id=body.get("counterparty_id", ""),
                    status=body.get("status", "passed"),
                ),
                status=201,
            )
        if action == "classify":
            return json_response(
                ctp.classify_risk(
                    counterparty_id=body.get("counterparty_id", ""),
                    risk_level=body.get("risk_level", "medium"),
                ),
                status=201,
            )
        mapping = {
            "vendor": ctp.register_vendor,
            "customer": ctp.register_customer,
            "partner": ctp.register_partner,
        }
        if action in mapping:
            return json_response(mapping[action](**kwargs), status=201)
        return json_response(
            ctp.register(counterparty_type=body.get("counterparty_type", "other"), **kwargs),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cp_aml_handler(request: web.Request) -> web.Response:
    try:
        aml = _suite().aml
        if request.method == "GET":
            return json_response(aml.status())
        body = await _read_json(request)
        action = body.get("action", "sanctions")
        if action == "pep":
            return json_response(
                aml.register_pep(
                    name=body.get("name", ""),
                    role=body.get("role", ""),
                    country=body.get("country", ""),
                ),
                status=201,
            )
        if action == "score":
            return json_response(
                aml.aml_score(
                    counterparty_id=body.get("counterparty_id", ""),
                    name=body.get("name", ""),
                    score=float(body.get("score", 40) or 40),
                ),
                status=201,
            )
        if action == "watchlist":
            return json_response(
                aml.watchlist(
                    name=body.get("name", ""),
                    list_name=body.get("list_name", "internal"),
                    hit=bool(body.get("hit", False)),
                ),
                status=201,
            )
        if action == "high_risk":
            return json_response(
                aml.detect_high_risk(
                    entity_name=body.get("entity_name", ""),
                    reason=body.get("reason", ""),
                ),
                status=201,
            )
        if action == "transaction":
            return json_response(
                aml.review_transaction(
                    transaction_ref=body.get("transaction_ref", ""),
                    amount=float(body.get("amount", 0) or 0),
                    counterparty_id=body.get("counterparty_id", ""),
                    status=body.get("status", "cleared"),
                ),
                status=201,
            )
        return json_response(
            aml.monitor_sanctions(
                name=body.get("name", ""),
                list_name=body.get("list_name", "UN"),
                matched=bool(body.get("matched", False)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cp_risk_handler(request: web.Request) -> web.Response:
    try:
        risk = _suite().risk
        if request.method == "GET":
            return json_response(risk.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "assess":
            findings = body.get("findings") if isinstance(body.get("findings"), list) else None
            return json_response(
                risk.assess_compliance_risk(
                    title=body.get("title", ""),
                    score=float(body.get("score", 50) or 50),
                    findings=findings,
                ),
                status=201,
            )
        if action == "contract":
            return json_response(
                risk.correlate_contract_risk(
                    contract_ref=body.get("contract_ref", ""),
                    risk_id=body.get("risk_id", ""),
                    detail=body.get("detail", ""),
                ),
                status=201,
            )
        if action == "reg_change":
            return json_response(
                risk.regulatory_change_impact(
                    change_title=body.get("change_title", ""),
                    impact=body.get("impact", "medium"),
                    detail=body.get("detail", ""),
                ),
                status=201,
            )
        if action == "heatmap":
            return json_response(risk.heatmap(scope=body.get("scope", "enterprise")), status=201)
        if action == "prioritize":
            return json_response(
                risk.prioritize(
                    risk_id=body.get("risk_id", ""),
                    priority=body.get("priority", "high"),
                ),
                status=201,
            )
        if action == "mitigate":
            actions = body.get("actions") if isinstance(body.get("actions"), list) else None
            return json_response(
                risk.recommend_mitigation(risk_id=body.get("risk_id", ""), actions=actions),
                status=201,
            )
        return json_response(
            risk.register_risk(
                title=body.get("title", ""),
                category=body.get("category", "compliance"),
                likelihood=body.get("likelihood", "medium"),
                impact=body.get("impact", "medium"),
                company_id=body.get("company_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cp_ai_handler(request: web.Request) -> web.Response:
    try:
        ai = _suite().ai
        if request.method == "GET":
            return json_response(ai.status())
        body = await _read_json(request)
        action = body.get("action", "health")
        mapping = {
            "gaps": lambda: ai.detect_gaps(company_id=body.get("company_id", "")),
            "policy_conflicts": ai.detect_policy_conflicts,
            "regulatory_change": lambda: ai.monitor_regulatory_change(
                change_title=body.get("change_title", "")
            ),
            "health": ai.compliance_health_score,
            "governance": ai.governance_score,
            "recommend": ai.recommend,
            "report": lambda: ai.nl_report(audience=body.get("audience", "executive")),
        }
        if action not in mapping:
            return json_response({"error": f"unknown action: {action}"}, status=400)
        return json_response(mapping[action](), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def cp_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dtype = request.rel_url.query.get("type", "compliance")
        if request.method == "POST":
            body = await _read_json(request)
            dtype = body.get("dashboard_type", dtype)
        return json_response(_suite().dashboard.render(dashboard_type=dtype))
    except Exception as exc:
        return _handle_error(exc)


async def cp_knowledge_handler(request: web.Request) -> web.Response:
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
