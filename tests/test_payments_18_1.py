"""Tests — Payments Platform (Sprint 18.1)."""

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


def test_version_payments_ready():
    health = finance_enterprise.health()
    assert health["application_version"] == "5.1.4-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v5.1.3-enterprise"
    assert health["banking_platform_ready"] is True
    assert health["digital_wallets_ready"] is True
    assert health["payment_engine_ready"] is True
    assert health["cash_management_ready"] is True
    assert health["general_ledger_ready"] is True


def test_banking_wallets_payments():
    suite = finance_enterprise.payments
    bank = suite.banking.register_bank(name="QA Bank", bic="QABANKXX")
    acct = suite.banking.register_account(
        bank_id=bank["bank_id"], account_name="QA Ops", iban="US00QA0001"
    )
    wal = suite.wallets.create_wallet(owner_ref="org:qa", wallet_type="enterprise")
    suite.wallets.credit(wallet_id=wal["wallet_id"], amount=1000)
    pmt = suite.payments.create_payment(
        payment_type="outgoing", amount=100, from_ref=wal["wallet_id"], external_key="QA-1"
    )
    assert acct["bank_account_id"] and pmt["payment_id"]
    with pytest.raises(ValidationError):
        suite.payments.create_payment(
            payment_type="outgoing", amount=50, from_ref=wal["wallet_id"], external_key="QA-1"
        )


def test_cash_approvals_bootstrap():
    suite = finance_enterprise.payments
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "5.1.4-enterprise"
    assert boot["bank_id"] and boot["approval_id"] and boot["register_id"]
    assert suite.processing.approve(
        payment_id=boot["outgoing_payment_id"], approver="controller", decision="approved"
    )["decision"] == "approved"
    for dtype in ("payments", "wallets", "banking", "cash"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_payments(client):
    health = await client.get(f"{PAY}/health")
    body = await health.json()
    assert body["application_version"] == "5.1.4-enterprise"
    assert body["banking_platform_ready"] is True
    assert body["payment_engine_ready"] is True

    boot = await client.post(f"{PAY}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    approve = await client.post(
        f"{PAY}/processing",
        json={
            "action": "approve",
            "payment_id": boot_body["scheduled_payment_id"],
            "approver": "cfo",
        },
    )
    assert approve.status == 201

    cash = await client.post(
        f"{PAY}/cash",
        json={"action": "operate", "register_id": boot_body["register_id"], "operation": "in", "amount": 25},
    )
    assert cash.status == 201

    resp = await client.get(f"{PREFIX}/health")
    assert resp.status == 200
    assert (await resp.json())["application_version"] == "5.1.4-enterprise"


def test_docs_and_regression_18_1():
    for name in (
        "BANKING_PLATFORM.md",
        "DIGITAL_WALLETS.md",
        "PAYMENT_ENGINE.md",
        "CASH_MANAGEMENT.md",
        "FINANCIAL_CONTROLS.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "PAYMENTS_PLATFORM.md").exists()
    assert (ROOT / "applications" / "finance_enterprise" / "payments" / "facade.py").exists()
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
    assert "5.1.4-enterprise" in manifest
    assert "18.4" in manifest
