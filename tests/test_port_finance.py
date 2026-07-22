"""Tests — Port ERP Finance & Commercial Management (Sprint 9.7)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.port_erp import port_erp
from applications.port_erp.api.register import register_port_erp_routes
from applications.port_erp.finance.models import (
    CommercialContract,
    CommercialTariff,
    ContractPartyType,
    CustomerAccount,
    ExchangeRate,
    ExpenseRecord,
    FeeType,
    PricingMode,
    TaxRate,
)
from applications.port_erp.shared.models import Customer


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_port_erp_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    port_erp.reset()
    yield
    port_erp.reset()


def test_version_finance_docs_bridges():
    health = port_erp.health()
    assert health["application_version"] == "2.0.0"
    assert health["finance_engine"] == "1.0"
    assert "finance" in health
    docs = Path(__file__).resolve().parents[1] / "docs" / "PORT_FINANCE.md"
    assert docs.exists()
    assert "Finance Engine" in docs.read_text(encoding="utf-8")
    assert port_erp.platform.platform_health()["platform_dependency"] == "AI Platform Core v3"
    assert port_erp.ecosystem.ecosystem_health()["ecosystem_dependency"] == "AI Ecosystem v1.5"
    root = Path(__file__).resolve().parents[1] / "applications" / "port_erp"
    for name in (
        "finance",
        "billing",
        "contracts",
        "tariffs",
        "invoices",
        "payments",
        "accounting",
        "suppliers",
        "currencies",
        "taxes",
        "budget",
        "profitability",
    ):
        assert (root / name).is_dir()


@pytest.mark.asyncio
async def test_billing_invoice_payment_flow():
    customer = port_erp.core.customers.register(Customer(name="Acme Trade"))
    port_erp.finance.tariffs.register(
        CommercialTariff(name="Berth day rate", fee_type=FeeType.BERTH, rate=1000, currency="USD")
    )
    port_erp.finance.tariffs.register(
        CommercialTariff(name="Storage TEU", fee_type=FeeType.STORAGE, rate=50)
    )
    port_erp.finance.taxes.register(TaxRate(name="VAT", rate_pct=16, country="KE"))

    bill = port_erp.finance.billing.create_bill(
        customer_id=customer.customer_id,
        charges=[
            {"fee_type": "berth_fees", "quantity": 2, "description": "2 days berth"},
            {"fee_type": "storage_fees", "quantity": 10},
        ],
        country="KE",
        company_id="portco-1",
    )
    assert bill.subtotal == 2500
    assert bill.tax_total == 400  # 16% of 2500
    assert bill.total == 2900

    issued = await port_erp.finance.invoices.issue(bill.invoice_id)
    assert issued.status.value == "issued"

    partial = await port_erp.finance.payments.pay(invoice_id=bill.invoice_id, amount=1000)
    assert partial.status.value == "completed"
    mid = port_erp.finance.invoices.get(bill.invoice_id)
    assert mid.status.value == "partially_paid"

    await port_erp.finance.payments.pay(invoice_id=bill.invoice_id, amount=1900)
    paid = port_erp.finance.invoices.get(bill.invoice_id)
    assert paid.status.value == "paid"
    assert paid.to_dict()["outstanding"] == 0


@pytest.mark.asyncio
async def test_contracts_accounting_profitability():
    contract = port_erp.finance.contracts.create(
        CommercialContract(
            title="OceanLine SLA",
            party_type=ContractPartyType.SHIPPING_LINE,
            party_name="OceanLine",
            value=100000,
        )
    )
    active = await port_erp.finance.contracts.activate(contract.contract_id)
    assert active.status.value == "active"

    entries = port_erp.finance.accounting.post(
        debit_account="1100",
        credit_account="4000",
        amount=500,
        reference="inv-1",
        description="Revenue recognition",
        company_id="portco-1",
    )
    assert len(entries) == 2
    assert port_erp.finance.accounting.journal()

    port_erp.finance.currencies.set_rate(
        ExchangeRate(base_currency="USD", quote_currency="KES", rate=130)
    )
    assert port_erp.finance.accounting.convert(10, from_currency="USD", to_currency="KES") == 1300

    port_erp.finance.finance.record_expense(
        ExpenseRecord(cost_center="ops", company_id="portco-1", amount=200, category="fuel")
    )
    # Seed some paid revenue via invoice path
    customer = port_erp.core.customers.register(Customer(name="Rev Co"))
    port_erp.finance.tariffs.register(
        CommercialTariff(name="Port fee", fee_type=FeeType.PORT, rate=500)
    )
    bill = port_erp.finance.billing.create_bill(
        customer_id=customer.customer_id,
        charges=[{"fee_type": "port_fees", "quantity": 1}],
        company_id="portco-1",
    )
    await port_erp.finance.invoices.issue(bill.invoice_id)
    await port_erp.finance.payments.pay(invoice_id=bill.invoice_id, amount=bill.total)

    summary = port_erp.finance.profitability.summary(company_id="portco-1")
    assert summary["revenue"] == bill.total
    assert summary["expenses"] == 200
    assert summary["profit"] == round(bill.total - 200, 2)
    cash = port_erp.finance.finance.cash_flow(company_id="portco-1")
    assert cash["inflow"] == bill.total


@pytest.mark.asyncio
async def test_customer_account_and_tariff_modes():
    customer = port_erp.core.customers.register(Customer(name="Credit Co"))
    account = port_erp.finance.accounts.open_account(
        CustomerAccount(customer_id=customer.customer_id, credit_limit=50000)
    )
    assert account.to_dict()["available_credit"] == 50000

    port_erp.finance.tariffs.register(
        CommercialTariff(
            name="Emergency handling",
            fee_type=FeeType.HANDLING,
            rate=200,
            pricing_mode=PricingMode.EMERGENCY,
        )
    )
    quote = port_erp.finance.tariffs.quote(fee_type="handling_fees", quantity=2, emergency=True)
    assert quote["amount"] == 400
    assert "emergency" in port_erp.finance.tariffs.pricing_modes()


@pytest.mark.asyncio
async def test_finance_rest_api(client: TestClient):
    health = await client.get("/api/port/v1/health")
    assert health.status == 200
    body = await health.json()
    assert body["application_version"] == "2.0.0"
    assert body["finance_engine"] == "1.0"

    finance = await client.get("/api/port/v1/finance")
    assert finance.status == 200

    tariff = await client.post(
        "/api/port/v1/tariffs",
        json={"name": "API Berth", "fee_type": "berth_fees", "rate": 800},
    )
    assert tariff.status == 201

    cust = await client.post(
        "/api/port/v1/finance/accounts",
        json={"customer_name": "API Customer", "credit_limit": 10000},
    )
    assert cust.status == 201
    account = await cust.json()

    bill = await client.post(
        "/api/port/v1/billing",
        json={
            "customer_id": account["customer_id"],
            "charges": [{"fee_type": "berth_fees", "quantity": 1}],
        },
    )
    assert bill.status == 201
    invoice = await bill.json()

    issued = await client.post(f"/api/port/v1/invoices/{invoice['invoice_id']}/issue")
    assert issued.status == 200

    pay = await client.post(
        "/api/port/v1/payments",
        json={"invoice_id": invoice["invoice_id"], "amount": invoice["total"]},
    )
    assert pay.status == 201

    contract = await client.post(
        "/api/port/v1/contracts",
        json={"title": "API Contract", "party_type": "customer", "party_name": "API Customer"},
    )
    assert contract.status == 201
    contract_body = await contract.json()
    activated = await client.post(f"/api/port/v1/contracts/{contract_body['contract_id']}/activate")
    assert activated.status == 200

    journal = await client.post(
        "/api/port/v1/accounting/entries",
        json={"debit_account": "1100", "credit_account": "4000", "amount": 100},
    )
    assert journal.status == 201
    books = await client.get("/api/port/v1/accounting")
    assert books.status == 200
