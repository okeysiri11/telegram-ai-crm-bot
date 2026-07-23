"""Tests — Treasury Platform (Sprint 18.3)."""

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
TR = "/api/finance-tr/v1"


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


def test_version_treasury_ready():
    health = finance_enterprise.health()
    assert health["application_version"] == "5.1.7-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v5.1.6-enterprise"
    assert health["treasury_platform_ready"] is True
    assert health["budget_management_ready"] is True
    assert health["financial_planning_ready"] is True
    assert health["ai_financial_forecasting_ready"] is True
    assert health["invoice_platform_ready"] is True


def test_treasury_budget_recon():
    suite = finance_enterprise.treasury
    pool = suite.treasury.create_pool(name="QA Pool", balance=100000)
    bud = suite.budgets.create_budget(
        name="QA Dept", budget_type="department", amount=50000
    )
    stmt = suite.reconciliation.import_statement(
        account_ref="QA-BANK", period="2026-07", lines=[{"memo": "x", "amount": 10, "external_id": "1"}]
    )
    assert pool["pool_id"] and bud["budget_id"] and stmt["statement_id"]
    with pytest.raises(ValidationError):
        suite.budgets.create_budget(name="", budget_type="department", amount=1)


def test_forecast_ai_bootstrap():
    suite = finance_enterprise.treasury
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "5.1.7-enterprise"
    assert boot["pool_id"] and boot["cash_forecast_id"] and boot["ai_nl_id"]
    assert suite.ai.nl_summary(audience="board")["insight_type"] == "nl_summary"
    for dtype in ("treasury", "budget", "forecast", "liquidity", "planning"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_treasury(client):
    health = await client.get(f"{TR}/health")
    body = await health.json()
    assert body["application_version"] == "5.1.7-enterprise"
    assert body["treasury_platform_ready"] is True
    assert body["budget_management_ready"] is True

    boot = await client.post(f"{TR}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    fc = await client.post(
        f"{TR}/forecast",
        json={"kind": "liquidity", "horizon_days": 30, "projected": 1000},
    )
    assert fc.status == 201

    ai = await client.post(
        f"{TR}/ai",
        json={"action": "nl_summary", "audience": "cfo"},
    )
    assert ai.status == 201

    for prefix in (PREFIX, PAY, BIL):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "5.1.7-enterprise"

    assert boot_body["workspace_id"]


def test_docs_and_regression_18_3():
    for name in (
        "TREASURY_PLATFORM.md",
        "BUDGET_MANAGEMENT.md",
        "BANK_RECONCILIATION.md",
        "FINANCIAL_PLANNING.md",
        "AI_FINANCIAL_FORECASTING.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "TREASURY_PLATFORM.md").exists()
    assert (ROOT / "applications" / "finance_enterprise" / "treasury" / "facade.py").exists()
    assert (ROOT / "applications" / "finance_enterprise" / "billing" / "facade.py").exists()

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
    assert "5.1.7-enterprise" in manifest
    assert "18.7" in manifest
