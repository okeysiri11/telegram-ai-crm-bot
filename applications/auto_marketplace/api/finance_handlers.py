# Finance API handlers — Sprint 6.5.

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.middleware import json_response
from applications.auto_marketplace.finance.models import Contract, FinancePayment, FinanceRole, PurchaseAgreement
from applications.auto_marketplace.shared.exceptions import AuthorizationError


def _check_finance_perm(request: web.Request, permission: str = "finance.read") -> None:
    principal = request.get("principal") or {}
    role = principal.get("role", FinanceRole.FINANCE_MANAGER.value)
    if not auto_marketplace.finance_engine.security.authorize(role, permission):
        raise AuthorizationError(f"Permission denied: {permission}")


async def finance_metrics_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.finance_engine.metrics())


async def list_document_templates_handler(request: web.Request) -> web.Response:
    _check_finance_perm(request, "documents.read")
    items = auto_marketplace.finance_engine.documents.list_templates(category=request.query.get("category", ""))
    return json_response({"items": [t.to_dict() for t in items]})


async def generate_document_handler(request: web.Request) -> web.Response:
    _check_finance_perm(request, "documents.manage")
    data = await request.json()
    doc = await auto_marketplace.finance_engine.documents.generate_from_template(
        data["template_id"],
        title=data.get("title", ""),
        variables=data.get("variables", {}),
        customer_id=data.get("customer_id", ""),
        deal_id=data.get("deal_id", ""),
    )
    return json_response(doc.to_dict(), status=201)


async def get_document_handler(request: web.Request) -> web.Response:
    _check_finance_perm(request, "documents.read")
    doc = auto_marketplace.finance_engine.documents.get(request.match_info["document_id"])
    return json_response(doc.to_dict())


async def approve_document_handler(request: web.Request) -> web.Response:
    _check_finance_perm(request, "documents.manage")
    doc = auto_marketplace.finance_engine.documents.approve(request.match_info["document_id"])
    return json_response(doc.to_dict())


async def export_document_handler(request: web.Request) -> web.Response:
    _check_finance_perm(request, "documents.read")
    return json_response(auto_marketplace.finance_engine.documents.export_document(request.match_info["document_id"]))


async def create_contract_handler(request: web.Request) -> web.Response:
    _check_finance_perm(request, "contracts.manage")
    data = await request.json()
    contract = PurchaseAgreement(
        customer_id=data.get("customer_id", ""),
        dealer_id=data.get("dealer_id", ""),
        vehicle_id=data.get("vehicle_id", ""),
        deal_id=data.get("deal_id", ""),
        amount=float(data.get("amount", 0)),
        currency=data.get("currency", "USD"),
        terms=data.get("terms", {}),
    )
    created = await auto_marketplace.finance_engine.contracts.create_purchase_agreement(contract)
    return json_response(created.to_dict(), status=201)


async def get_contract_handler(request: web.Request) -> web.Response:
    _check_finance_perm(request, "contracts.read")
    contract = auto_marketplace.finance_engine.contracts.get(request.match_info["contract_id"])
    return json_response(contract.to_dict())


async def sign_contract_handler(request: web.Request) -> web.Response:
    _check_finance_perm(request, "contracts.manage")
    data = await request.json()
    contract = await auto_marketplace.finance_engine.contracts.sign(
        request.match_info["contract_id"],
        signed_by=data.get("signed_by", "customer"),
    )
    return json_response(contract.to_dict())


async def analyze_contract_handler(request: web.Request) -> web.Response:
    _check_finance_perm(request, "contracts.read")
    analysis = await auto_marketplace.finance_engine.contracts.analyze(request.match_info["contract_id"])
    return json_response(analysis)


async def create_payment_handler(request: web.Request) -> web.Response:
    _check_finance_perm(request, "payments.manage")
    data = await request.json()
    payment = FinancePayment(
        deal_id=data.get("deal_id", ""),
        customer_id=data.get("customer_id", ""),
        dealer_id=data.get("dealer_id", ""),
        amount=float(data.get("amount", 0)),
        currency=data.get("currency", "USD"),
        method_id=data.get("method_id", ""),
    )
    created = await auto_marketplace.finance_engine.payments.create_payment(payment)
    return json_response(created.to_dict(), status=201)


async def capture_payment_handler(request: web.Request) -> web.Response:
    _check_finance_perm(request, "payments.manage")
    payment = await auto_marketplace.finance_engine.payments.capture(request.match_info["payment_id"])
    invoice = await auto_marketplace.finance_engine.invoices.generate(
        deal_id=payment.deal_id,
        customer_id=payment.customer_id,
        dealer_id=payment.dealer_id,
        amount=payment.amount,
        currency=payment.currency,
    )
    receipt = auto_marketplace.finance_engine.receipts.generate(
        payment_id=payment.payment_id,
        invoice_id=invoice.invoice_id,
        customer_id=payment.customer_id,
        amount=payment.amount,
        currency=payment.currency,
    )
    auto_marketplace.finance_engine.invoices.mark_paid(invoice.invoice_id, payment_id=payment.payment_id)
    return json_response({"payment": payment.to_dict(), "invoice": invoice.to_dict(), "receipt": receipt.to_dict()})


async def generate_invoice_handler(request: web.Request) -> web.Response:
    _check_finance_perm(request, "invoices.manage")
    data = await request.json()
    invoice = await auto_marketplace.finance_engine.invoices.generate(
        deal_id=data.get("deal_id", ""),
        customer_id=data.get("customer_id", ""),
        dealer_id=data.get("dealer_id", ""),
        amount=float(data.get("amount", 0)),
        currency=data.get("currency", "USD"),
        jurisdiction=data.get("jurisdiction", "US"),
    )
    return json_response(invoice.to_dict(), status=201)


async def request_refund_handler(request: web.Request) -> web.Response:
    _check_finance_perm(request, "refunds.manage")
    data = await request.json()
    refund = await auto_marketplace.finance_engine.accounting.request_refund(
        payment_id=data["payment_id"],
        amount=float(data.get("amount", 0)),
        reason=data.get("reason", ""),
        currency=data.get("currency", "USD"),
    )
    return json_response(refund.to_dict(), status=201)


async def process_refund_handler(request: web.Request) -> web.Response:
    _check_finance_perm(request, "refunds.manage")
    refund = await auto_marketplace.finance_engine.accounting.process_refund(request.match_info["refund_id"])
    return json_response(refund.to_dict())


async def create_settlement_handler(request: web.Request) -> web.Response:
    _check_finance_perm(request, "settlements.manage")
    data = await request.json()
    settlement = auto_marketplace.finance_engine.accounting.create_settlement(
        dealer_id=data["dealer_id"],
        period_start=float(data.get("period_start", 0)),
        period_end=float(data.get("period_end", 0)),
        gross_amount=float(data.get("gross_amount", 0)),
        commission_total=float(data.get("commission_total", 0)),
        currency=data.get("currency", "USD"),
    )
    return json_response(settlement.to_dict(), status=201)


async def complete_settlement_handler(request: web.Request) -> web.Response:
    _check_finance_perm(request, "settlements.manage")
    settlement = await auto_marketplace.finance_engine.accounting.complete_settlement(request.match_info["settlement_id"])
    return json_response(settlement.to_dict())


async def financial_report_handler(_request: web.Request) -> web.Response:
    _check_finance_perm(_request, "reports.view")
    report = await auto_marketplace.finance_engine.reports.generate_summary()
    return json_response(report.to_dict())


async def audit_log_handler(request: web.Request) -> web.Response:
    _check_finance_perm(request, "finance.read")
    resource_id = request.query.get("resource_id")
    records = auto_marketplace.finance_engine.security.list_audit(resource_id=resource_id)
    return json_response({"items": [r.to_dict() for r in records]})
