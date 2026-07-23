"""Tests — Finance Enterprise Foundation (Sprint 18.0 / Bidex)."""

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
LE = "/api/legal-enterprise/v1"
LEC = "/api/legal-enterprise-certification/v1"


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


def test_version_finance_enterprise_ready():
    health = finance_enterprise.health()
    assert health["application_version"] == "5.1.6-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v5.1.5-enterprise"
    assert health["finance_enterprise_foundation_ready"] is True
    assert health["general_ledger_ready"] is True
    assert health["financial_registry_ready"] is True
    assert health["multi_currency_ready"] is True
    assert health["financial_architecture_ready"] is True


def test_registry_and_currency():
    org = finance_enterprise.registry.register_organization(name="Bidex QA Org")
    ccy = finance_enterprise.registry.register_currency(code="usd", name="US Dollar")
    assert org["organization_id"] and ccy["code"] == "USD"
    rate = finance_enterprise.currency.register_rate(
        from_currency="USD", to_currency="EUR", rate=0.9
    )
    conv = finance_enterprise.currency.convert(amount=100, from_currency="USD", to_currency="EUR")
    assert rate["rate_id"] and conv["converted_amount"] == 90.0
    with pytest.raises(ValidationError):
        finance_enterprise.registry.register_organization(name="")
    with pytest.raises(ValidationError):
        finance_enterprise.currency.register_rate(from_currency="USD", to_currency="EUR", rate=0)


def test_ledger_and_knowledge():
    boot = finance_enterprise.bootstrap()
    assert boot["journal_id"] and boot["trial_balance_id"] and boot["organization_id"]
    assert boot["version"] == "5.1.6-enterprise"
    assert finance_enterprise.ledger.status()["postings"] >= 2
    bal = finance_enterprise.ledger.balance(account_code="1000")
    assert bal["debit"] == 100000
    assert finance_enterprise.knowledge.status()["entries"] >= 4
    with pytest.raises(ValidationError):
        finance_enterprise.ledger.create_journal_entry(
            description="unbalanced",
            lines=[
                {"account_code": "1000", "debit": 10, "credit": 0},
                {"account_code": "3000", "debit": 0, "credit": 5},
            ],
        )
    for dtype in ("overview", "accounts", "cash", "currency", "health"):
        assert finance_enterprise.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_finance_enterprise(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "5.1.6-enterprise"
    assert body["general_ledger_ready"] is True
    assert body["financial_registry_ready"] is True

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    je = await client.post(
        f"{PREFIX}/ledger",
        json={
            "action": "journal",
            "description": "Record revenue",
            "lines": [
                {"account_code": "1100", "debit": 500, "credit": 0},
                {"account_code": "4000", "debit": 0, "credit": 500},
            ],
        },
    )
    assert je.status == 201
    je_body = await je.json()
    posted = await client.post(
        f"{PREFIX}/ledger",
        json={"action": "post", "journal_id": je_body["journal_id"]},
    )
    assert posted.status == 201

    fx = await client.post(
        f"{PREFIX}/currency",
        json={"action": "convert", "amount": 50, "from_currency": "USD", "to_currency": "EUR"},
    )
    assert fx.status == 201

    dash = await client.get(f"{PREFIX}/dashboard?dashboard_type=overview")
    assert dash.status == 200
    assert (await dash.json())["dashboard_type"] == "overview"

    assert boot_body["organization_id"]


def test_docs_and_regression_18_0():
    for name in (
        "FINANCE_ENTERPRISE.md",
        "GENERAL_LEDGER.md",
        "FINANCIAL_ARCHITECTURE.md",
        "MULTI_CURRENCY.md",
        "FINANCIAL_API.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "FINANCE_ENTERPRISE.md").exists()
    assert (ROOT / "applications" / "finance_enterprise" / "application.py").exists()
    assert (ROOT / "applications" / "finance_enterprise" / "ledger.py").exists()

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
    assert "5.1.6-enterprise" in manifest
    assert "18.6" in manifest
