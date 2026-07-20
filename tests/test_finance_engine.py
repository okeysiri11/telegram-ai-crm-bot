"""Tests — Documents, Contracts & Financial Operations (Sprint 6.5)."""

from __future__ import annotations

import asyncio

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.finance.models import FinancePayment, FinanceRole, PurchaseAgreement
from applications.auto_marketplace.finance.security import finance_security


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_auto_marketplace_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    auto_marketplace.reset()
    yield
    auto_marketplace.reset()


def test_finance_security_roles():
    assert finance_security.authorize(FinanceRole.OWNER, "finance.delete")
    assert finance_security.authorize(FinanceRole.FINANCE_MANAGER, "invoices.manage")
    assert not finance_security.authorize(FinanceRole.CUSTOMER, "refunds.manage")


@pytest.mark.asyncio
async def test_document_generation():
    templates = auto_marketplace.finance_engine.documents.list_templates()
    assert len(templates) >= 1
    doc = await auto_marketplace.finance_engine.documents.generate_from_template(
        templates[0].template_id,
        title="Test Purchase Doc",
        variables={"vehicle": "Toyota Camry", "amount": "28000", "currency": "USD", "invoice_id": "1", "total": "28000"},
        customer_id="c1",
    )
    assert doc.document_id
    assert doc.pdf_url


@pytest.mark.asyncio
async def test_contract_lifecycle():
    agreement = PurchaseAgreement(customer_id="c1", dealer_id="d1", vehicle_id="v1", amount=32000)
    created = await auto_marketplace.finance_engine.contracts.create_purchase_agreement(agreement)
    signed = await auto_marketplace.finance_engine.contracts.sign(created.contract_id, signed_by="customer-1")
    assert signed.status.value == "signed"


@pytest.mark.asyncio
async def test_payment_invoice_receipt_flow():
    payment = FinancePayment(deal_id="deal-1", customer_id="c1", amount=25000, currency="USD")
    created = await auto_marketplace.finance_engine.payments.create_payment(payment)
    captured = await auto_marketplace.finance_engine.payments.capture(created.payment_id)
    assert captured.status == "completed"
    invoice = await auto_marketplace.finance_engine.invoices.generate(
        deal_id="deal-1", customer_id="c1", amount=25000
    )
    assert invoice.total_amount > invoice.amount
    receipt = auto_marketplace.finance_engine.receipts.generate(
        payment_id=captured.payment_id,
        invoice_id=invoice.invoice_id,
        customer_id="c1",
        amount=captured.amount,
    )
    assert receipt.receipt_id


@pytest.mark.asyncio
async def test_refund_and_settlement():
    refund = await auto_marketplace.finance_engine.accounting.request_refund(
        payment_id="pay-1", amount=500, reason="overcharge"
    )
    processed = await auto_marketplace.finance_engine.accounting.process_refund(refund.refund_id)
    assert processed.status.value == "processed"
    settlement = auto_marketplace.finance_engine.accounting.create_settlement(
        dealer_id="d1", period_start=0, period_end=9999999999, gross_amount=100000, commission_total=5000
    )
    completed = await auto_marketplace.finance_engine.accounting.complete_settlement(settlement.settlement_id)
    assert completed.status.value == "completed"


@pytest.mark.asyncio
async def test_commission_and_report():
    auto_marketplace.finance_engine.billing.calculate_commission(
        deal_id="deal-1", agent_id="a1", dealer_id="d1", sale_amount=40000
    )
    report = await auto_marketplace.finance_engine.reports.generate_summary()
    assert "total_invoiced" in report.metrics


@pytest.mark.asyncio
async def test_finance_api(client: TestClient):
    resp = await client.get("/api/auto/v1/finance/metrics", headers={"Authorization": "Bearer test"})
    assert resp.status == 200

    templates_resp = await client.get("/api/auto/v1/finance/documents/templates", headers={"Authorization": "Bearer test"})
    templates = (await templates_resp.json())["items"]
    resp = await client.post(
        "/api/auto/v1/finance/documents/generate",
        json={"template_id": templates[0]["template_id"], "variables": {"vehicle": "BMW", "amount": "50000", "currency": "USD", "invoice_id": "1", "total": "50000"}, "customer_id": "c1"},
        headers={"Authorization": "Bearer test"},
    )
    assert resp.status == 201

    resp = await client.post(
        "/api/auto/v1/finance/contracts",
        json={"customer_id": "c1", "dealer_id": "d1", "vehicle_id": "v1", "amount": 30000},
        headers={"Authorization": "Bearer test"},
    )
    assert resp.status == 201


@pytest.mark.asyncio
async def test_document_created_event():
    received: list = []
    from events import subscribe

    subscribe("DocumentCreatedEvent", lambda e: received.append(e))
    templates = auto_marketplace.finance_engine.documents.list_templates()
    await auto_marketplace.finance_engine.documents.generate_from_template(
        templates[0].template_id, title="Event Doc", variables={"vehicle": "X", "amount": "1", "currency": "USD", "invoice_id": "1", "total": "1"}
    )
    await asyncio.sleep(0.05)
    assert len(received) >= 1
