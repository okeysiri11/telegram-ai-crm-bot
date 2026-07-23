"""API handlers — Billing Platform (Sprint 18.2)."""

from __future__ import annotations

from aiohttp import web

from applications.finance_enterprise import finance_enterprise
from applications.finance_enterprise.api.middleware import json_response
from applications.finance_enterprise.shared.exceptions import NotFoundError, ValidationError


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
    return finance_enterprise.billing


async def bil_health_handler(request: web.Request) -> web.Response:
    health = finance_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "invoice_platform_ready": health.get("invoice_platform_ready"),
            "accounts_receivable_ready": health.get("accounts_receivable_ready"),
            "accounts_payable_ready": health.get("accounts_payable_ready"),
            "tax_engine_ready": health.get("tax_engine_ready"),
            "cash_flow_intelligence_ready": health.get("cash_flow_intelligence_ready"),
            "suite": _suite().status(),
        }
    )


async def bil_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def bil_invoices_handler(request: web.Request) -> web.Response:
    try:
        invoices = _suite().invoices
        if request.method == "GET":
            return json_response(invoices.status())
        body = await _read_json(request)
        action = body.get("action", "create")
        if action == "template":
            return json_response(
                invoices.create_template(name=body.get("name", ""), body=body.get("body", "")),
                status=201,
            )
        if action == "credit_note":
            return json_response(
                invoices.credit_note(
                    invoice_id=body.get("invoice_id", ""),
                    amount=float(body.get("amount", 0) or 0),
                    reason=body.get("reason", ""),
                ),
                status=201,
            )
        if action == "debit_note":
            return json_response(
                invoices.debit_note(
                    invoice_id=body.get("invoice_id", ""),
                    amount=float(body.get("amount", 0) or 0),
                    reason=body.get("reason", ""),
                ),
                status=201,
            )
        if action == "issue":
            return json_response(invoices.issue(invoice_id=body.get("invoice_id", "")), status=201)
        return json_response(
            invoices.create_invoice(
                customer_ref=body.get("customer_ref", ""),
                amount=float(body.get("amount", 0) or 0),
                currency=body.get("currency", "USD"),
                invoice_type=body.get("invoice_type", "standard"),
                tax_amount=float(body.get("tax_amount", 0) or 0),
                due_on=body.get("due_on", ""),
                template_id=body.get("template_id", ""),
                lines=body.get("lines") if isinstance(body.get("lines"), list) else None,
                recurrence=body.get("recurrence", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def bil_quotations_handler(request: web.Request) -> web.Response:
    try:
        quotations = _suite().quotations
        if request.method == "GET":
            return json_response(quotations.status())
        body = await _read_json(request)
        action = body.get("action", "create")
        if action == "template":
            return json_response(
                quotations.create_template(name=body.get("name", ""), body=body.get("body", "")),
                status=201,
            )
        if action == "approve":
            return json_response(
                quotations.approve(
                    quotation_id=body.get("quotation_id", ""),
                    approver=body.get("approver", "sales"),
                ),
                status=201,
            )
        if action == "convert":
            return json_response(
                quotations.convert_to_invoice(
                    quotation_id=body.get("quotation_id", ""),
                    invoices=_suite().invoices,
                ),
                status=201,
            )
        return json_response(
            quotations.create(
                customer_ref=body.get("customer_ref", ""),
                amount=float(body.get("amount", 0) or 0),
                currency=body.get("currency", "USD"),
                template_id=body.get("template_id", ""),
                valid_until=body.get("valid_until", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def bil_receivables_handler(request: web.Request) -> web.Response:
    try:
        receivables = _suite().receivables
        if request.method == "GET":
            return json_response(receivables.status())
        body = await _read_json(request)
        action = body.get("action", "open")
        if action == "aging":
            return json_response(
                receivables.aging(customer_ref=body.get("customer_ref", "")),
                status=201,
            )
        if action == "collect":
            return json_response(
                receivables.collect(
                    receivable_id=body.get("receivable_id", ""),
                    step=body.get("step", "reminder"),
                ),
                status=201,
            )
        if action == "allocate":
            return json_response(
                receivables.allocate(
                    receivable_id=body.get("receivable_id", ""),
                    amount=float(body.get("amount", 0) or 0),
                    payment_ref=body.get("payment_ref", ""),
                ),
                status=201,
            )
        if action == "overdue":
            return json_response(
                receivables.mark_overdue(receivable_id=body.get("receivable_id", "")),
                status=201,
            )
        return json_response(
            receivables.open_receivable(
                customer_ref=body.get("customer_ref", ""),
                invoice_id=body.get("invoice_id", ""),
                amount=float(body.get("amount", 0) or 0),
                currency=body.get("currency", "USD"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def bil_payables_handler(request: web.Request) -> web.Response:
    try:
        payables = _suite().payables
        if request.method == "GET":
            return json_response(payables.status())
        body = await _read_json(request)
        action = body.get("action", "bill")
        if action == "schedule":
            return json_response(
                payables.schedule_payment(
                    bill_id=body.get("bill_id", ""),
                    schedule_at=body.get("schedule_at", ""),
                    amount=float(body["amount"]) if body.get("amount") is not None else None,
                ),
                status=201,
            )
        if action == "approve":
            return json_response(
                payables.approve(
                    bill_id=body.get("bill_id", ""),
                    approver=body.get("approver", ""),
                    decision=body.get("decision", "approved"),
                ),
                status=201,
            )
        if action == "liabilities":
            return json_response(payables.liabilities(), status=201)
        if action == "reconcile":
            return json_response(
                payables.reconcile_statement(
                    vendor_ref=body.get("vendor_ref", ""),
                    statement_total=float(body.get("statement_total", 0) or 0),
                    note=body.get("note", ""),
                ),
                status=201,
            )
        return json_response(
            payables.register_bill(
                vendor_ref=body.get("vendor_ref", ""),
                amount=float(body.get("amount", 0) or 0),
                currency=body.get("currency", "USD"),
                due_on=body.get("due_on", ""),
                description=body.get("description", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def bil_tax_handler(request: web.Request) -> web.Response:
    try:
        tax = _suite().tax
        if request.method == "GET":
            return json_response(tax.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "calculate":
            return json_response(
                tax.calculate(
                    taxable_amount=float(body.get("taxable_amount", 0) or 0),
                    rate=float(body.get("rate", 0) or 0),
                    tax_type=body.get("tax_type", "vat"),
                ),
                status=201,
            )
        if action == "rule":
            return json_response(
                tax.add_rule(
                    code=body.get("code", ""),
                    jurisdiction=body.get("jurisdiction", ""),
                    rate=float(body.get("rate", 0) or 0),
                    detail=body.get("detail", ""),
                ),
                status=201,
            )
        if action == "report":
            return json_response(tax.report(period=body.get("period", "2026-Q3")), status=201)
        if action == "summary":
            return json_response(tax.summary(), status=201)
        return json_response(
            tax.register_tax(
                code=body.get("code", ""),
                name=body.get("name", ""),
                rate=float(body.get("rate", 0) or 0),
                tax_type=body.get("tax_type", "vat"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def bil_cashflow_handler(request: web.Request) -> web.Response:
    try:
        cashflow = _suite().cashflow
        if request.method == "GET":
            return json_response(cashflow.status())
        body = await _read_json(request)
        action = body.get("action", "receipt")
        if action == "payment":
            return json_response(
                cashflow.expected_payments(
                    amount=float(body.get("amount", 0) or 0),
                    due_on=body.get("due_on", ""),
                    source_ref=body.get("source_ref", ""),
                ),
                status=201,
            )
        if action == "forecast":
            return json_response(
                cashflow.forecast(
                    horizon_days=int(body.get("horizon_days", 30) or 30),
                    kind=body.get("kind", "cash"),
                ),
                status=201,
            )
        return json_response(
            cashflow.expected_receipts(
                amount=float(body.get("amount", 0) or 0),
                due_on=body.get("due_on", ""),
                source_ref=body.get("source_ref", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def bil_ai_handler(request: web.Request) -> web.Response:
    try:
        ai = _suite().ai
        if request.method == "GET":
            return json_response(ai.status())
        body = await _read_json(request)
        action = body.get("action", "insight")
        if action == "nl_summary":
            return json_response(ai.nl_summary(audience=body.get("audience", "executive")), status=201)
        return json_response(
            ai.insight(
                insight_type=body.get("insight_type", "late_payment"),
                subject=body.get("subject", ""),
                score=float(body.get("score", 0.7) or 0.7),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def bil_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dashboard = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("dashboard_type", "invoice")
            return json_response(dashboard.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dashboard.render(dashboard_type=body.get("dashboard_type", "invoice")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def bil_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                base=body.get("base", "invoice"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
