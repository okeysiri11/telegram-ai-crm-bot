"""Tests — Billing Platform (Sprint 18.2)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.finance_enterprise import finance_enterprise
from applications.finance_enterprise.api.register import register_finance_enterprise_routes
from applications.finance_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/finance-enterprise/v1"
PAY = "/api/finance-pay/v1"
BIL = "/api/finance-bil/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_finance_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    finance_enterprise.reset()
    yield
    finance_enterprise.reset()


def test_version_billing_ready():
    health = finance_enterprise.health()
    assert health["application_version"] == "5.2.0-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v5.1.7-enterprise"
    assert health["invoice_platform_ready"] is True
    assert health["accounts_receivable_ready"] is True
    assert health["accounts_payable_ready"] is True
    assert health["tax_engine_ready"] is True
    assert health["cash_flow_intelligence_ready"] is True
    assert health["payment_engine_ready"] is True


def test_invoice_tax_receivable_payable():
    suite = finance_enterprise.billing
    inv = suite.invoices.create_invoice(customer_ref="cust:qa", amount=1000, tax_amount=200)
    suite.invoices.issue(invoice_id=inv["invoice_id"])
    calc = suite.tax.calculate(taxable_amount=1000, rate=0.2)
    assert calc["tax_amount"] == 200.0
    ar = suite.receivables.open_receivable(
        customer_ref="cust:qa", invoice_id=inv["invoice_id"], amount=1200
    )
    bill = suite.payables.register_bill(vendor_ref="vend:qa", amount=500)
    assert ar["receivable_id"] and bill["bill_id"]
    with pytest.raises(ValidationError):
        suite.invoices.create_invoice(customer_ref="", amount=10)


def test_cashflow_ai_bootstrap():
    suite = finance_enterprise.billing
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "5.2.0-enterprise"
    assert boot["converted_invoice_id"] and boot["tax_calc_id"] and boot["cash_forecast_id"]
    assert suite.ai.nl_summary(audience="board")["insight_type"] == "nl_summary"
    for dtype in ("invoice", "receivables", "payables", "tax", "cashflow"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_billing(client):
    health = await client.get(f"{BIL}/health")
    body = await health.json()
    assert body["application_version"] == "5.2.0-enterprise"
    assert body["invoice_platform_ready"] is True
    assert body["tax_engine_ready"] is True

    boot = await client.post(f"{BIL}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    tax = await client.post(
        f"{BIL}/tax",
        json={"action": "calculate", "taxable_amount": 100, "rate": 0.1},
    )
    assert tax.status == 201

    ai = await client.post(
        f"{BIL}/ai",
        json={"action": "nl_summary", "audience": "cfo"},
    )
    assert ai.status == 201

    for prefix in (PREFIX, PAY):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "5.2.0-enterprise"

    assert boot_body["receivable_id"]


def test_docs_and_regression_18_2():
    for name in (
        "INVOICING_PLATFORM.md",
        "ACCOUNTS_RECEIVABLE.md",
        "ACCOUNTS_PAYABLE.md",
        "TAX_ENGINE.md",
        "CASH_FLOW_INTELLIGENCE.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "BILLING_PLATFORM.md").exists()
    assert (ROOT / "applications" / "finance_enterprise" / "billing" / "facade.py").exists()
    assert (ROOT / "applications" / "finance_enterprise" / "payments" / "facade.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_enterprise.config import DEFAULT_CONFIG as PORT
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP
    from applications.crypto_enterprise.config import DEFAULT_CONFIG as CRYPTO
    from applications.legal_enterprise.config import DEFAULT_CONFIG as LEGAL

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT.application_version == "4.6.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    assert CRYPTO.application_version == "4.8.0-enterprise"
    assert LEGAL.application_version == "5.0.0-enterprise"
    manifest = (ROOT / "applications" / "finance_enterprise" / "manifest.json").read_text()
    assert "5.2.0-enterprise" in manifest
    assert "18.8" in manifest
