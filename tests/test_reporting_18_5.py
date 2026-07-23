"""Tests — Financial Reporting & BI (Sprint 18.5)."""

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
DA = "/api/finance-da/v1"
RPT = "/api/finance-rpt/v1"


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


def test_version_reporting_ready():
    health = finance_enterprise.health()
    assert health["application_version"] == "5.2.0-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v5.1.7-enterprise"
    assert health["financial_reporting_ready"] is True
    assert health["business_intelligence_ready"] is True
    assert health["executive_analytics_ready"] is True
    assert health["enterprise_bi_ready"] is True
    assert health["digital_asset_treasury_ready"] is True
    assert health["engines"]["reporting"] == "1.0"


def test_statements_and_kpis():
    suite = finance_enterprise.reporting
    bs = suite.statements.generate(
        statement_type="balance_sheet",
        period="2026-Q3",
        totals={"assets": 100, "liabilities": 40, "equity": 60},
    )
    kpi = suite.intelligence.register_kpi(name="QA Margin", kpi_type="margin", value=40)
    assert bs["statement_id"] and kpi["kpi_id"]
    with pytest.raises(ValidationError):
        suite.statements.generate(statement_type="balance_sheet", period="")


def test_forecast_ai_bootstrap():
    suite = finance_enterprise.reporting
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "5.2.0-enterprise"
    assert boot["balance_sheet_id"] and boot["forecast_revenue_id"] and boot["ai_nl_id"]
    assert suite.forecasting.forecast(kind="profit", projected=100)["kind"] == "profit"
    assert suite.ai.nl_report(audience="cfo")["insight_type"] == "nl_report"
    for dtype in ("executive", "kpi", "profitability", "forecast", "enterprise_bi"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_reporting(client):
    health = await client.get(f"{RPT}/health")
    body = await health.json()
    assert body["application_version"] == "5.2.0-enterprise"
    assert body["financial_reporting_ready"] is True
    assert body["enterprise_bi_ready"] is True

    boot = await client.post(f"{RPT}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    fc = await client.post(
        f"{RPT}/forecast",
        json={"kind": "liquidity", "horizon_days": 30, "projected": 1000},
    )
    assert fc.status == 201

    ai = await client.post(
        f"{RPT}/ai",
        json={"action": "nl_report", "audience": "board"},
    )
    assert ai.status == 201

    for prefix in (PREFIX, PAY, BIL, TR, DA):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "5.2.0-enterprise"

    assert boot_body["executive_summary_id"]


def test_docs_and_regression_18_5():
    for name in (
        "FINANCIAL_REPORTING.md",
        "BUSINESS_INTELLIGENCE.md",
        "EXECUTIVE_ANALYTICS.md",
        "FINANCIAL_KPI.md",
        "ENTERPRISE_REPORTING.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "FINANCIAL_REPORTING.md").exists()
    assert (ROOT / "applications" / "finance_enterprise" / "reporting" / "facade.py").exists()
    assert (ROOT / "applications" / "finance_enterprise" / "digital_assets" / "facade.py").exists()

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
