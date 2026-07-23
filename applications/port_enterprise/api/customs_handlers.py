"""API handlers — Customs & Trade (Sprint 15.4)."""

from __future__ import annotations

from aiohttp import web

from applications.port_enterprise import port_enterprise
from applications.port_enterprise.api.middleware import json_response
from applications.port_enterprise.shared.exceptions import NotFoundError, ValidationError


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
    return port_enterprise.customs_trade


async def ct_health_handler(request: web.Request) -> web.Response:
    health = port_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "customs_platform_ready": health.get("customs_platform_ready"),
            "border_control_ready": health.get("border_control_ready"),
            "international_trade_ready": health.get("international_trade_ready"),
            "trade_compliance_ready": health.get("trade_compliance_ready"),
            "ai_trade_intelligence_ready": health.get("ai_trade_intelligence_ready"),
            "suite": _suite().status(),
        }
    )


async def ct_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ct_customs_handler(request: web.Request) -> web.Response:
    try:
        customs = _suite().customs
        if request.method == "GET":
            return json_response(customs.status())
        body = await _read_json(request)
        action = body.get("action", "office")
        if action == "declare":
            return json_response(
                customs.declare(
                    declaration_type=body.get("declaration_type", "import"),
                    reference=body.get("reference", ""),
                    office_id=body.get("office_id", ""),
                    hs_code=body.get("hs_code", ""),
                    value=float(body.get("value", 0) or 0),
                ),
                status=201,
            )
        if action == "hs":
            return json_response(
                customs.register_hs_code(
                    code=body.get("code", ""),
                    description=body.get("description", ""),
                    duty_rate=float(body.get("duty_rate", 0) or 0),
                ),
                status=201,
            )
        if action == "tariff":
            return json_response(
                customs.set_tariff(
                    hs_code=body.get("hs_code", ""),
                    country=body.get("country", ""),
                    rate=float(body.get("rate", 0) or 0),
                ),
                status=201,
            )
        if action == "duty":
            return json_response(
                customs.calculate_duty(
                    declaration_id=body.get("declaration_id", ""),
                    duty_rate=float(body.get("duty_rate", 0) or 0),
                    tax_rate=float(body.get("tax_rate", 0.2) or 0.2),
                ),
                status=201,
            )
        if action == "clear":
            return json_response(
                customs.clear(body.get("declaration_id", ""), status=body.get("status", "cleared")),
                status=201,
            )
        return json_response(
            customs.register_office(
                name=body.get("name", ""),
                code=body.get("code", ""),
                country=body.get("country", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ct_border_handler(request: web.Request) -> web.Response:
    try:
        border = _suite().border
        if request.method == "GET":
            return json_response(border.status())
        body = await _read_json(request)
        action = body.get("action", "checkpoint")
        if action == "cargo":
            return json_response(
                border.inspect_cargo(
                    checkpoint_id=body.get("checkpoint_id", ""),
                    cargo_ref=body.get("cargo_ref", ""),
                    result=body.get("result", "pass"),
                ),
                status=201,
            )
        if action == "vehicle":
            return json_response(
                border.inspect_vehicle(
                    checkpoint_id=body.get("checkpoint_id", ""),
                    plate=body.get("plate", ""),
                    result=body.get("result", "pass"),
                ),
                status=201,
            )
        if action == "container":
            return json_response(
                border.inspect_container(
                    checkpoint_id=body.get("checkpoint_id", ""),
                    container_ref=body.get("container_ref", ""),
                    result=body.get("result", "pass"),
                ),
                status=201,
            )
        if action == "seal":
            return json_response(
                border.verify_seal(
                    container_ref=body.get("container_ref", ""),
                    seal_no=body.get("seal_no", ""),
                    intact=bool(body.get("intact", True)),
                ),
                status=201,
            )
        if action == "risk":
            return json_response(
                border.risk_inspect(
                    checkpoint_id=body.get("checkpoint_id", ""),
                    subject_ref=body.get("subject_ref", ""),
                    risk_score=float(body.get("risk_score", 0) or 0),
                ),
                status=201,
            )
        if action == "crossing":
            return json_response(
                border.crossing(
                    checkpoint_id=body.get("checkpoint_id", ""),
                    direction=body.get("direction", "in"),
                    subject_ref=body.get("subject_ref", ""),
                ),
                status=201,
            )
        return json_response(
            border.register_checkpoint(name=body.get("name", ""), border=body.get("border", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ct_trade_handler(request: web.Request) -> web.Response:
    try:
        trade = _suite().trade
        if request.method == "GET":
            return json_response(trade.status())
        body = await _read_json(request)
        action = body.get("action", "import")
        if action == "export":
            return json_response(
                trade.register_export(
                    reference=body.get("reference", ""),
                    destination_country=body.get("destination_country", ""),
                    value=float(body.get("value", 0) or 0),
                ),
                status=201,
            )
        if action == "country":
            return json_response(
                trade.register_country(code=body.get("code", ""), name=body.get("name", "")),
                status=201,
            )
        if action == "partner":
            return json_response(
                trade.register_partner(
                    name=body.get("name", ""),
                    country=body.get("country", ""),
                    role=body.get("role", "buyer"),
                ),
                status=201,
            )
        if action == "agreement":
            parties = body.get("parties") if isinstance(body.get("parties"), list) else None
            return json_response(
                trade.trade_agreement(name=body.get("name", ""), parties=parties),
                status=201,
            )
        if action == "incoterm":
            return json_response(
                trade.set_incoterm(trade_ref=body.get("trade_ref", ""), incoterm=body.get("incoterm", "FOB")),
                status=201,
            )
        if action == "lc":
            return json_response(
                trade.letter_of_credit(
                    reference=body.get("reference", ""),
                    amount=float(body.get("amount", 0) or 0),
                    bank=body.get("bank", ""),
                ),
                status=201,
            )
        if action == "invoice":
            return json_response(
                trade.commercial_invoice(
                    trade_ref=body.get("trade_ref", ""),
                    amount=float(body.get("amount", 0) or 0),
                    currency=body.get("currency", "USD"),
                ),
                status=201,
            )
        if action == "packing":
            return json_response(
                trade.packing_list(
                    trade_ref=body.get("trade_ref", ""),
                    packages=int(body.get("packages", 1) or 1),
                    weight_kg=float(body.get("weight_kg", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            trade.register_import(
                reference=body.get("reference", ""),
                origin_country=body.get("origin_country", ""),
                value=float(body.get("value", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ct_compliance_handler(request: web.Request) -> web.Response:
    try:
        compliance = _suite().compliance
        if request.method == "GET":
            return json_response(compliance.status())
        body = await _read_json(request)
        action = body.get("action", "sanctions")
        if action == "restricted":
            return json_response(
                compliance.register_restricted(hs_code=body.get("hs_code", ""), reason=body.get("reason", "")),
                status=201,
            )
        if action == "dual_use":
            return json_response(
                compliance.dual_use(
                    item_ref=body.get("item_ref", ""),
                    controlled=bool(body.get("controlled", True)),
                ),
                status=201,
            )
        if action == "license":
            return json_response(
                compliance.license(
                    license_no=body.get("license_no", ""),
                    license_type=body.get("license_type", "import"),
                    expires_at=body.get("expires_at", ""),
                ),
                status=201,
            )
        if action == "certificate":
            return json_response(
                compliance.certificate(
                    cert_type=body.get("cert_type", "origin"),
                    reference=body.get("reference", ""),
                    issuer=body.get("issuer", ""),
                ),
                status=201,
            )
        if action == "audit":
            return json_response(
                compliance.audit(
                    entity_type=body.get("entity_type", ""),
                    entity_id=body.get("entity_id", ""),
                    action=body.get("audit_action", body.get("event", "review")),
                ),
                status=201,
            )
        if action == "report":
            return json_response(
                compliance.compliance_report(period=body.get("period", "monthly")),
                status=201,
            )
        return json_response(
            compliance.screen_sanctions(
                party_name=body.get("party_name", ""),
                country=body.get("country", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ct_documents_handler(request: web.Request) -> web.Response:
    try:
        documents = _suite().documents
        if request.method == "GET":
            return json_response(documents.status())
        body = await _read_json(request)
        action = body.get("action", "store")
        if action == "sign":
            return json_response(
                documents.sign(body.get("document_id", ""), signer=body.get("signer", "")),
                status=201,
            )
        return json_response(
            documents.store_document(
                doc_type=body.get("doc_type", "other"),
                title=body.get("title", ""),
                reference=body.get("reference", ""),
                trade_ref=body.get("trade_ref", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ct_ai_handler(request: web.Request) -> web.Response:
    try:
        ai = _suite().ai
        if request.method == "GET":
            return json_response(ai.status())
        body = await _read_json(request)
        action = body.get("action", "risk")
        if action == "delay":
            return json_response(
                ai.delay_predict(
                    declaration_id=body.get("declaration_id", ""),
                    risk=float(body.get("risk", 0.2) or 0.2),
                ),
                status=201,
            )
        if action == "validate":
            return json_response(
                ai.validate_document(
                    document_id=body.get("document_id", ""),
                    valid=bool(body.get("valid", True)),
                ),
                status=201,
            )
        if action == "trade_opt":
            return json_response(ai.optimize_trade(corridor=body.get("corridor", "")), status=201)
        if action == "tariff":
            return json_response(
                ai.optimize_tariff(
                    hs_code=body.get("hs_code", ""),
                    baseline_rate=float(body.get("baseline_rate", 0) or 0),
                ),
                status=201,
            )
        if action == "congestion":
            return json_response(
                ai.congestion_predict(checkpoint_id=body.get("checkpoint_id", "")),
                status=201,
            )
        if action == "fraud":
            return json_response(
                ai.fraud_detect(
                    trade_ref=body.get("trade_ref", ""),
                    anomaly_score=float(body.get("anomaly_score", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            ai.compliance_risk(party=body.get("party", ""), score=float(body.get("score", 0) or 0)),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ct_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("type", "customs")
            return json_response(dash.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dash.render(dashboard_type=body.get("dashboard_type", "customs")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ct_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                registry_type=body.get("registry_type", "trade"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
